ARG BASE_REGISTRY=registry.redhat.io
ARG BASE_IMAGE=rhel9/python-311
ARG BASE_TAG=1-66.1720018730

################
# App Base
# Installs and sets up poetry environment variables
################
FROM ${BASE_REGISTRY}/${BASE_IMAGE}:${BASE_TAG} AS base

ENV APP_ROOT=/opt/app-root \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    TZ=Asia/Singapore \
    CNB_STACK_ID=com.redhat.stacks.ubi9-python-311 \
    CNB_USER_ID=1001 \
    CNB_GROUP_ID=0 \
    POETRY_REQUESTS_TIMEOUT=300 \
    POETRY_VERSION=1.8.3 \
    # make poetry create the virtual environment in the project's root
    # it gets named `.venv`
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    # do not ask any interactive question
    POETRY_NO_INTERACTION=1 \
    # this is where our requirements + virtual environment will live
    VENV_PATH="$APP_ROOT/.venv"

# prepend venv to path
ENV PATH="$VENV_PATH/bin:$PATH"

RUN chown -R 1001:0 $APP_ROOT \
    && python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir poetry==$POETRY_VERSION

# copy project requirement files here to ensure they will be cached.
WORKDIR $APP_ROOT
COPY --chown=1001:0 poetry.lock pyproject.toml ./

################
# Development
# Sets up environment for code development
################

FROM base AS development

COPY docker-scripts/ /usr/bin

# install runtime deps - uses $POETRY_VIRTUALENVS_IN_PROJECT internally
# --no-root is used to just install dependencies as development code will be mounted
RUN poetry install --no-root \
    && rm -rf $HOME/.cache/pypoetry/artifacts \
    && rm -rf $HOME/.cache/pypoetry/cache \
    # Poetry creates folders that requires permission fixes
    && fix-permissions ${APP_ROOT} -P \
    && rpm-file-permissions

# The following echo adds the unset command for the variables set below to the \
# venv activation script. This is inspired from scl_enable script and prevents \
# the virtual environment to be activated multiple times and also every time \
# the prompt is rendered.
RUN echo "unset BASH_ENV PROMPT_COMMAND ENV" >> $VENV_PATH/bin/activate

USER 1001

WORKDIR /opt/app-root

# For RHEL/Centos 8+ scl_enable isn't sourced automatically in s2i-core
# so virtualenv needs to be activated this way
ENV BASH_ENV="$VENV_PATH/bin/activate" \
    ENV="$VENV_PATH/bin/activate" \
    PROMPT_COMMAND=". $VENV_PATH/bin/activate"

################
# App Build
# Sets up poetry bundle to be exported to the actual app
# Should only be used after development is completed and tested
################

FROM base AS app-build

WORKDIR /opt/app-root
COPY --chown=1001:0 asr_inference_service/ /opt/app-root/asr_inference_service/

# installs poetry bundle plugin and bundles the app into the /venv directory
RUN poetry self add poetry-plugin-bundle \
    && poetry bundle venv --only=main /opt/app-root/venv

################
# App
# Import bundled environment into a
# fresh image copy void of other build dependencies
################

FROM ${BASE_REGISTRY}/${BASE_IMAGE}:${BASE_TAG} AS app

ENV APP_ROOT=/opt/app-root \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    TZ=Asia/Singapore \
    CNB_STACK_ID=com.redhat.stacks.ubi9-python-311 \
    CNB_USER_ID=1001 \
    CNB_GROUP_ID=0

RUN chown -R 1001:0 $APP_ROOT
COPY --chown=1001:0 --from=app-build /opt/app-root/venv $APP_ROOT/venv

USER 1001

# The following echo adds the unset command for the variables set below to the \
# venv activation script. This is inspired from scl_enable script and prevents \
# the virtual environment to be activated multiple times and also every time \
# the prompt is rendered.
RUN echo "unset BASH_ENV PROMPT_COMMAND ENV" >> $APP_ROOT/venv/bin/activate

# For RHEL/Centos 8+ scl_enable isn't sourced automatically in s2i-core
# so virtualenv needs to be activated this way
ENV BASH_ENV="$APP_ROOT/venv/bin/activate" \
    ENV="$APP_ROOT/venv/bin/activate" \
    PROMPT_COMMAND=". $APP_ROOT/venv/bin/activate"

ENV PRETRAINED_MODEL_DIR=$APP_ROOT/pretrained_models
ENV SAMPLE_RATE=16000

EXPOSE 8080

WORKDIR $APP_ROOT
CMD ["start"]

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
CMD curl -s http://localhost:8080/health || exit 1

################
# Prod
# import model weights into the app image
################

FROM app AS prod

COPY --chown=1001:0 pretrained_models/whisper-small/ $APP_ROOT/pretrained_models/

WORKDIR $APP_ROOT
CMD ["start"]

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
CMD curl -s http://localhost:8080/health || exit 1
