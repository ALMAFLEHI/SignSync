# Sprint 2.11 Rework Recording Commands

These 22 commands cover only the approved Sprint 2.11 rework recordings:

- document R01-R10
- signature R01-R10
- account_number R01
- atm R01

Run them manually from the project root after applying the safe cleanup.

```powershell
python ml/src/collect_video.py --participant P02 --label document --repetition 1 --camera-index 1 --notes "Sprint 2.11 banking intent expansion"
python ml/src/collect_video.py --participant P02 --label document --repetition 2 --camera-index 1 --notes "Sprint 2.11 banking intent expansion"
python ml/src/collect_video.py --participant P02 --label document --repetition 3 --camera-index 1 --notes "Sprint 2.11 banking intent expansion"
python ml/src/collect_video.py --participant P02 --label document --repetition 4 --camera-index 1 --notes "Sprint 2.11 banking intent expansion"
python ml/src/collect_video.py --participant P02 --label document --repetition 5 --camera-index 1 --notes "Sprint 2.11 banking intent expansion"
python ml/src/collect_video.py --participant P02 --label document --repetition 6 --camera-index 1 --notes "Sprint 2.11 banking intent expansion"
python ml/src/collect_video.py --participant P02 --label document --repetition 7 --camera-index 1 --notes "Sprint 2.11 banking intent expansion"
python ml/src/collect_video.py --participant P02 --label document --repetition 8 --camera-index 1 --notes "Sprint 2.11 banking intent expansion"
python ml/src/collect_video.py --participant P02 --label document --repetition 9 --camera-index 1 --notes "Sprint 2.11 banking intent expansion"
python ml/src/collect_video.py --participant P02 --label document --repetition 10 --camera-index 1 --notes "Sprint 2.11 banking intent expansion"
python ml/src/collect_video.py --participant P02 --label signature --repetition 1 --camera-index 1 --notes "Sprint 2.11 banking intent expansion"
python ml/src/collect_video.py --participant P02 --label signature --repetition 2 --camera-index 1 --notes "Sprint 2.11 banking intent expansion"
python ml/src/collect_video.py --participant P02 --label signature --repetition 3 --camera-index 1 --notes "Sprint 2.11 banking intent expansion"
python ml/src/collect_video.py --participant P02 --label signature --repetition 4 --camera-index 1 --notes "Sprint 2.11 banking intent expansion"
python ml/src/collect_video.py --participant P02 --label signature --repetition 5 --camera-index 1 --notes "Sprint 2.11 banking intent expansion"
python ml/src/collect_video.py --participant P02 --label signature --repetition 6 --camera-index 1 --notes "Sprint 2.11 banking intent expansion"
python ml/src/collect_video.py --participant P02 --label signature --repetition 7 --camera-index 1 --notes "Sprint 2.11 banking intent expansion"
python ml/src/collect_video.py --participant P02 --label signature --repetition 8 --camera-index 1 --notes "Sprint 2.11 banking intent expansion"
python ml/src/collect_video.py --participant P02 --label signature --repetition 9 --camera-index 1 --notes "Sprint 2.11 banking intent expansion"
python ml/src/collect_video.py --participant P02 --label signature --repetition 10 --camera-index 1 --notes "Sprint 2.11 banking intent expansion"
python ml/src/collect_video.py --participant P02 --label account_number --repetition 1 --camera-index 1 --notes "Sprint 2.11 banking intent expansion"
python ml/src/collect_video.py --participant P02 --label atm --repetition 1 --camera-index 1 --notes "Sprint 2.11 banking intent expansion"
```
