#!/bin/bash

header(){
    echo "============================================"
    echo "       LEVELOPS PLUGINS AUTOSETUP"
    echo "============================================"
    echo ""
}
print_help(){
    header
    echo "Description:   Installation script for the LevelOps Plugins."
    echo "               The installation directory will be created if it doesn't exist."
    echo ""
    echo ""
    echo "Usage:"
    echo "         ./autosestup.sh /path/to/installation/dir"
    echo ""
    echo "Options:"
    echo ""
    echo "    -h   --help     Prints this help."
}
install_plugins(){
    echo ""
    header
    echo "Installing the LevelOps Plugins at '${INSTALLATION_DIR}'"
    echo ""
    echo ""
    echo "....................."
    echo ""
    # exit 0

    mkdir -p ${INSTALLATION_DIR}
    git clone --depth 1 https://github.com/levelops-tools-admin/levelops-plugins ${INSTALLATION_DIR}
    if pip3;
    then
        pip3 install virtualenv # in some environments pip3 is available instead of pip
    else
        pip install virtualenv
    fi
    mkdir -p ${INSTALLATION_DIR}/env
    virtualenv ${INSTALLATION_DIR}/env
    source ${INSTALLATION_DIR}/env/bin/activate
    pip install -r ${INSTALLATION_DIR}/requirements.txt
}

if [ $# -lt 1 ];
then
    echo "**************************************************************************"
    echo "   Please specify the path were the LevelOps plugins will be installed."
    echo "**************************************************************************"
    read USER_INPUT
    if [ -z ${USER_INPUT} ]; then
        echo ""
        print_help
        exit 1
    else
        INSTALLATION_DIR=${USER_INPUT}
    fi
else
    INSTALLATION_DIR=${1}
fi

if [ ${INSTALLATION_DIR} == '--help' ] || [ ${INSTALLATION_DIR} == '-h' ] || [[ ${INSTALLATION_DIR} = -* ]];
then
    print_help
    exit 1
fi

install_plugins