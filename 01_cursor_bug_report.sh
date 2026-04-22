export CURSOR_API_KEY="${CURSOR_API_KEY:?Set CURSOR_API_KEY}"
# read prompt.yaml
prompt=$(cat ../../bug_report.yaml)
cursor-agent -p --force --output-format stream-json --stream-partial-output --model gpt-5.2 "$prompt"


echo "01_cursor_bug_report.sh completed"