#!/usr/bin/env bash
# ============================================================
# Stop All Website Servers
# ============================================================
# 모든 웹사이트 서버를 중단합니다.
#
# 사용법:
#   ./stop_all_servers.sh              # 모든 사이트 중단
#   ./stop_all_servers.sh airbnb       # 특정 사이트만 중단
#   ./stop_all_servers.sh airbnb ebay  # 여러 사이트 중단
#
# 옵션 (환경변수):
#   DRY_RUN=1        실제로 중단하지 않고 어떤 작업을 할지만 출력
#   USE_RESET=1      reset_servers.sh 실행 (DB 초기화 가능성 있음)
#   REMOVE_VOLUMES=1 docker compose down -v (데이터 손실 가능)
#
# 예시:
#   DRY_RUN=1 ./stop_all_servers.sh    # 미리보기
#   ./stop_all_servers.sh              # 실제 중단
# ============================================================

set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

exec "$ROOT_DIR/tools/stop_all_sites.sh" "$@"



