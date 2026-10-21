# Biblix-Prompt (Biblix Design). Abschalten in der App "Biblix Design" unter Terminal.
# Farben folgen dem Konsole-Schema "Biblix" (Blau = Akzentfarbe, Gelb = Zweitakzent).
if [ -n "$PS1" ] && [ -n "$BASH_VERSION" ]; then
    __biblix_prompt() {
        local s=$?
        local a='\[\e[1;34m\]' g='\[\e[1;33m\]' r='\[\e[1;31m\]' l='\[\e[2m\]' n='\[\e[0m\]'
        local zeichen="${g}>_${n}"
        [ "$s" -ne 0 ] && zeichen="${r}>_${n}"
        PS1="${a}\u${n}${l}@${n}${a}\h${n} ${l}\w${n}\n${zeichen} "
    }
    case "$PROMPT_COMMAND" in
        *__biblix_prompt*) ;;
        *) PROMPT_COMMAND="__biblix_prompt${PROMPT_COMMAND:+; $PROMPT_COMMAND}" ;;
    esac
fi
