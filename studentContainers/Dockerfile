FROM quay.io/jupyter/minimal-notebook:latest

COPY ./customPromptExtension/extension /extension/customPrompt
COPY ./genericSupportExtension/extension /extension/genericSupport
COPY ./noSupportExtension/extension /extension/noSupport
COPY ./personalizedSupportExtension/extension /extension/personalizedSupport
COPY ./extensionManager/extension /extension/extensionManager

USER root

RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g yarn

RUN pip install nbgitpuller
    
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

RUN git clone https://github.com/KaiYakexi/jupy-cell-lock.git /jupy-cell-lock && \
    cd /jupy-cell-lock && \
    pip install .

RUN jupyter labextension list
        
RUN jupyter labextension disable @jupyterlab/extensionmanager-extension

USER ${NB_USER}