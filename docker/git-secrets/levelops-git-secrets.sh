#!/usr/bin/env bash

# existing current
# existing historic
# new current
# new historic

init_git_secrets(){
    git-secrets --install -f
}

init_providers(){
    git secrets --register-aws
}

scan(){
    # git secrets --scan
    # scan_mode = "$1"
    case "$1" in
        current)
            git secrets --scan --no-index 2>&1
            ;;
        historic)
            git secrets --scan-history 2>&1
            ;;
    esac
}

cleanup(){
    sed -i 's/git\ssecrets.*//g' .git/hooks/commit-msg
    sed -i 's/git\ssecrets.*//g' .git/hooks/pre-commit
    sed -i 's/git\ssecrets.*//g' .git/hooks/prepare-commit-msg
}

no_git_secrets_scan(){
    log=$(init_git_secrets)
    log=$(init_providers)
    scan $1
    cleanup
}

existing_git_secrets_scan(){
    scan $1
}

# cd into work dir
cd $3
case "$1" in
    new)
        no_git_secrets_scan $2
        exit 0
        ;;
    existing)
        existing_git_secrets_scan $2
        exit 0
        ;;
    cleanup)
        cleanup
        ;;
    *)
        echo "Nothing"
        exit 1
        ;;
esac