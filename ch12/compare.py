"""여러 버전에 같은 시험을 실행하고 결과를 나란히 보여 준다."""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RESULTS = Path("compare-results.json")  # 실행할 때마다 한 회씩 쌓인다
LINE = re.compile(r"^([a-z]\d\d) (통과|실패|방어|뚫림)", re.M)
SKIP = shutil.ignore_patterns("logs", "review", "compare", "__pycache__")


def start(version, command):
    """프로젝트 사본에서 한 버전의 시험을 시작한다."""
    folder = tempfile.mkdtemp(prefix=f"v{version}-")
    shutil.copytree(".", folder, dirs_exist_ok=True, ignore=SKIP)
    env = dict(os.environ, AGENT_VERSION=str(version))
    job = subprocess.Popen(
        [sys.executable, "managed_eval.py", *command], cwd=folder, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return job, folder


def keep(version, folder):
    """답 전체가 든 결과 파일을 compare 폴더로 옮겨 둔다."""
    Path("compare").mkdir(exist_ok=True)
    for name in ("eval-results.json", "attack-results.json"):
        if Path(folder, name).exists():
            shutil.copy(Path(folder, name), f"compare/v{version}-{name}")


def main(versions):
    results = json.loads(RESULTS.read_text()) if RESULTS.exists() else {}
    jobs = [(version, start(version, command))
            for version in versions for command in ([], ["attack"])]
    for version, (job, folder) in jobs:  # 동시에 실행하고 차례로 기다린다
        output = job.communicate()[0]
        keep(version, folder)
        scores = results.setdefault(str(version), {})
        for case, word in LINE.findall(output):
            passed, total = scores.get(case, [0, 0])
            scores[case] = [passed + (word in ("통과", "방어")), total + 1]
    RESULTS.write_text(json.dumps(results, indent=1))

    names = [str(version) for version in versions]
    cases = sorted({case for name in names for case in results[name]})
    print("문제   " + "   ".join(f"버전 {name}" for name in names))
    for case in cases:
        cells = [results[name].get(case, [0, 0]) for name in names]
        if any(passed < total for passed, total in cells):  # 틀린 적 있는 문제만
            print(f"{case}    " + "     ".join(
                f"{passed}/{total}" for passed, total in cells))
    for name in names:
        passed = sum(p for p, _ in results[name].values())
        total = sum(t for _, t in results[name].values())
        print(f"버전 {name}: {passed}/{total} 통과")


if __name__ == "__main__":
    if "--new" in sys.argv:
        RESULTS.unlink(missing_ok=True)
    main([int(arg) for arg in sys.argv[1:] if arg.isdigit()])
