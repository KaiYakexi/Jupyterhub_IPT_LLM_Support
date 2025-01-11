FROM jupyter/datascience-notebook:latest

COPY ./extension /extension
USER root
RUN cd /extension && \
    pip install -ve . && \
    jlpm install && \
    jlpm run build && \
    cd .. && \
    rm -rf /extension 
        
USER ${NB_USER}

RUN jupyter labextension list
