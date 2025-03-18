FROM quay.io/jupyter/minimal-notebook:latest

COPY ./extension /extension

USER root
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g yarn
RUN cd /extension && \
    pip install -ve . && \
    jlpm && \
    jlpm install && \
    jlpm run build && \
    cd .. && \
    rm -rf /extension 
        
USER ${NB_USER}

RUN jupyter labextension list