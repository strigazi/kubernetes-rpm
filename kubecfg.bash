#!/bin/bash
#
# bash completion file for core kubecfg commands
#
# This script provides supports completion of:
#  - commands and their options
#  - container ids and names
#  - image repos and tags
#  - filepaths
#
# To enable the completions either:
#  - place this file in /etc/bash_completion.d
#  or
#  - copy this file and add the line below to your .bashrc after
#    bash completion features are loaded
#     . kubecfg.bash
#
# Note:
# Currently, the completions will not work if the kubecfg daemon is not
# bound to the default communication port/socket
# If the kubecfg daemon is using a unix socket for communication your user
# must have access to the socket for the completions to function correctly

__kubecfg_q() {
    kubecfg 2>/dev/null "$@"
}

__contains_word () {
    local w word=$1; shift
    for w in "$@"; do
        [[ $w = "$word" ]] && return
    done
}

__has_service() {
    for ((i=0; i < ${cword}; i++)); do
        local word=${words[i]}
        word=$(echo ${word} | awk -F"/" '{print $1}')
        if __contains_word "${words[i]}" "${services[@]}" &&
           ! __contains_word "${words[i-1]}" "${opts[@]}"; then
            return 0
        fi
    done
    return 1
}

__kubecfg_all_pods()
{
    local pods=($( __kubecfg_q list pods | tail -n +3 | awk {'print $1'} ))
    pods=${pods[@]/#/"pods/"}
    COMPREPLY=( $( compgen -W "${pods[*]}" -- "$cur" ) )
}

__kubecfg_all_minions()
{
    local minions=($( __kubecfg_q list minions | tail -n +3 | awk {'print $1'} ))
    minions=${minions[@]/#/"minions/"}
    COMPREPLY=( $( compgen -W "${minions[*]}" -- "$cur" ) )
}

__kubecfg_all_replicationControllers()
{
    local replicationControllers=($( __kubecfg_q list replicationControllers | tail -n +3 | awk {'print $1'} ))
    replicationControllers=${replicationControllers[@]/#/"replicationControllers/"}
    COMPREPLY=( $( compgen -W "${replicationControllers[*]}" -- "$cur" ) )
}

__kubecfg_all_services()
{
    local services=($( __kubecfg_q list services | tail -n +3 | awk {'print $1'} ))
    services=${services[@]/#/"services/"}
    COMPREPLY=( $( compgen -W "${services[*]}" -- "$cur" ) )
}

_kubecfg_specific_service_match()
{
    case "$cur" in
        pods/*)
            __kubecfg_all_pods
            ;;
        minions/*)
            __kubecfg_all_minions
            ;;
        replicationControllers/*)
            __kubecfg_all_replicationControllers
            ;;
        services/*)
            __kubecfg_all_services
            ;;
        *)
            if __has_service; then
                return 0
            fi
            compopt -o nospace
            COMPREPLY=( $( compgen -S / -W "${services[*]}" -- "$cur" ) )
            ;;
    esac
}

_kubecfg_get()
{
    _kubecfg_specific_service_match
}

_kubecfg_delete()
{
    _kubecfg_specific_service_match
}

_kubecfg_update()
{
    _kubecfg_specific_service_match
}

_kubecfg_service_match()
{
    if __has_service; then
        return 0
    fi

    case "$cur" in
        *)
            COMPREPLY=( $( compgen -W "${services[*]}" -- "$cur" ) )
            ;;
    esac
}

_kubecfg_list()
{
    _kubecfg_service_match
}

_kubecfg_create()
{
    _kubecfg_service_match
}

_kubecfg()
{
    local opts=(
            -h
            -c
    )
    local -A all_services=(
        [CREATE]="pods replicationControllers services"
        [UPDATE]="replicationControllers"
        [ALL]="pods replicationControllers services minions"
    )
    local services=(${all_services[ALL]})
    local -A all_commands=(
        [WITH_JSON]="create update"
        [ALL]="create update get list delete stop rm rollingupdate resize"
    )
    local commands=(${all_commands[ALL]})

    COMPREPLY=()
    local command
    local cur prev words cword
    _get_comp_words_by_ref -n : cur prev words cword

    if __contains_word "$prev" "${opts[@]}"; then
        case $prev in
            -h)
                comps=$(compgen -A hostname)
                return 0
                ;;
            -c)
                _filedir json
                return 0
                ;;
        esac
    fi

    if [[ "$cur" = -* ]]; then
        COMPREPLY=( $(compgen -W '${opts[*]}' -- "$cur") )
        return 0
    fi

    # if you passed -c, you are limited to create
    if __contains_word "-c" "${words[@]}"; then
        services=(${all_services[CREATE]} ${all_services[UPDATE]})
        commands=(${all_commands[WITH_JSON]})
    fi

    # figure out which command they are running, remembering that arguments to
    # options don't count as the command!  So a hostname named 'create' won't
    # trip things up
    for ((i=0; i < ${cword}; i++)); do
        if __contains_word "${words[i]}" "${commands[@]}" &&
           ! __contains_word "${words[i-1]}" "${opts[@]}"; then
            command=${words[i]}
            break
        fi
    done

    # tell the list of possible commands
    if [[ -z ${command} ]]; then
        COMPREPLY=( $( compgen -W "${commands[*]}" -- "$cur" ) )
        return 0
    fi

    # remove services which you can't update given your command
    if [[ ${command} == "create" ]]; then
        services=(${all_services[CREATE]})
    elif [[ ${command} == "update" ]]; then
        services=(${all_services[UPDATE]})
    fi

    # run the _kubecfg_${command} function to keep parsing
    local completions_func=_kubecfg_${command}
    declare -F $completions_func >/dev/null && $completions_func

    return 0
}

complete -F _kubecfg kubecfg
# ex: ts=4 sw=4 et filetype=sh
