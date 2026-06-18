@echo off
echo Egzersiz Tanima Modeli - Egitim
echo ================================
echo.
echo kagglefitnes/ klasoru taranacak, her video'dan pose ozellik cikarilacak.
echo Bu islem GPU yoksa UZUN surabilir (500-1000 video x 30fps).
echo.
python ml/exercise_recognizer.py --train
echo.
echo Bitti.
pause
