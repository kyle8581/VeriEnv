export CURSOR_API_KEY="${CURSOR_API_KEY:?Set CURSOR_API_KEY}"
# read prompt.yaml
prompt=$(cat ../../instruction_generation_and_validation.yaml)


# Track progress in real-time
cursor-agent -p --force --output-format stream-json --stream-partial-output   --model gpt-5.2 "$prompt"


echo "02_cursor_task_generation.sh completed"