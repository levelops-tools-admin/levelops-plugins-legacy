FROM alpine as base
RUN apk --update add --no-cache bash ncurses git less openssh && \
    rm -rf /var/lib/apt/lists/* 

FROM base
ARG branch=master
ENV PATH=/bin/:/git-secrets:$PATH
# git-secrets
RUN git clone --depth 1 --branch ${branch} https://github.com/awslabs/git-secrets.git /git-secrets
# levelops script
COPY levelops-git-secrets.sh /bin/levelops-git-secrets

WORKDIR /code

ENTRYPOINT [ "/bin/bash" ]