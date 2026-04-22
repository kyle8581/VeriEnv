export CURSOR_API_KEY="${CURSOR_API_KEY:?Set CURSOR_API_KEY}"
# read prompt.yaml
prompt=$(cat ../../prompt.yaml)

# Track progress in real-time by parsing JSON lines output from cursor-agent
cursor-agent -p --force --output-format stream-json --stream-partial-output --model gpt-5.2 "$prompt" 


echo "00_cursor_command.sh completed"