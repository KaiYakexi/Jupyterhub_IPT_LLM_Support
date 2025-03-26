FROM quay.io/jupyter/minimal-notebook:latest

COPY ./customPromptExtension/extension /extension/customPrompt
COPY ./genericSupportExtension/extension /extension/genericSupport
COPY ./noSupportExtension/extension /extension/noSupport
COPY ./personalizedSupportExtension/extension /extension/personalizedSupport
COPY ./extensionManager/extension /extension/extensionManager


USER root
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g yarn

RUN cd /extension/customPrompt && \
    pip install -ve . && \
    jlpm && \
    jlpm install && \
    jlpm run build && \
    cd .. && \
    rm -rf /extension/customPrompt

RUN cd /extension/genericSupport && \
    pip install -ve . && \
    jlpm && \
    jlpm install && \
    jlpm run build && \
    cd .. && \
    rm -rf /extension/genericSupport

RUN cd /extension/noSupport && \
    pip install -ve . && \
    jlpm && \
    jlpm install && \
    jlpm run build && \
    cd .. && \
    rm -rf /extension/noSupport

RUN cd /extension/personalizedSupport && \
    pip install -ve . && \
    jlpm && \
    jlpm install && \
    jlpm run build && \
    cd .. && \
    rm -rf /extension/personalizedSupport

RUN cd /extension/extensionManager && \
    pip install -ve . && \
    jlpm && \
    jlpm install && \
    jlpm run build && \
    cd .. && \
    rm -rf /extension/extensionManager
        
USER ${NB_USER}

RUN jupyter labextension list