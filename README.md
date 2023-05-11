# Detekce správně nasazené obličejové masky

Zde je dostupná implementace ukázkové aplikace diplomové práce na téma Detekce správně nasazené obličejové masky.

* **Autor:** Černý David
* **Vedoucí práce:** Ing. Karel Paleček, Ph.D.
* **Škola:** Technická univerzita v Liberci, Fakulta mechatroniky, informatiky a mezioborových studií

## Instalace
Zde je popsán detailní postup instalace aplikace.
### Prerekvizity

* **Nainstalovaný Python3 (aplikace testována na verzi 3.8.5)**
  * https://www.python.org/downloads/release/python-385/
* **Microsoft visual C++ build tools verze 14+**
  * https://visualstudio.microsoft.com/visual-cpp-build-tools/
* **Cmake**
  * https://cmake.org/download/
* **Funkční webkamera**
* **Nainstalovaná patřičná verze CUDA Toolkit pro výpočty GPU (v práci využitá verze 11.3)
  * https://developer.nvidia.com/cuda-downloads?target_os=Windows&target_arch=x86_64&target_version=11&target_type=exe_network
* **Nainstalovaná verze cudnn pro patřičnou verzi CUDA Toolkit
  * https://developer.nvidia.com/rdp/cudnn-download

### Postup

```
# clone this repository
git clone https://github.com/DavidCerny2737/DP.git
cd DP

# virtual environment and dependency install
python -m venv venv
venv\Scripts\activate
pip install -r requirments.txt
```
Dále je potřeba nainstalovat pytorch. Aplikace byla vyvýjena a testována s verzí torch 1.11.0 za použití cuda 11.3 a cpu
verze pytorch 1.11.0. Tato verze lze nainstalovat pomocí příkazu:
```
pip install torch==1.11.0+cu113 torchvision==0.12.0+cu113 torchaudio==0.11.0 --extra-index-url https://download.pytorch.org/whl/cu113
```
Ovšem program by měl fungovat i pod novější verzí. Příkazy na doinstalování lze navolit podle nabídky na:
https://pytorch.org/get-started/locally/ nebo použijte starší verzi pokud je to nutné.

Z https://1drv.ms/u/s!Apjyzhd1jsIxiKcFOwfVWhLR_hCJEA je třeba stáhnout soubor best.pt a vložit ho projektového adresáře.
Tento soubor obsahuje natrénované parametry detektoru YOLOv4-CSP.

Nakonec je potřeba dodefinovat flask proměnné pro aktuální session.
```
set FLASK_APP=app

# optional - for more verbose log
set FLASK_ENV=development 
```
## Konfigurace

Aplikace je konfigurtovatelná pomocí dictionary v app.py s názvem CONFIG. V defaultním provedení běží běží 
YOLOv4-CSP na CPU a je voláno v klasickém python runtime. Za zmínku stojí následující možnosti:

* device - definuje cíloový HW pro detekci:
  * '0' pro GPU
  * 'cpu' pro CPU
* onnx - definuje zda má být YOLOv4 spuštěno v rámci onnx gpu runtime z důvodu maximální optimalizace
  * True/False
* weights - definuje cestu k souboru best.pt

Velikost snímaných obrázků je možné upravit v main.js na řádku 16:
```
var width = 480;  // We will scale the photo width to this (note that only 160px steps are valid for yolov4-CSP - 640, 480, 320, ...)
```
Upravovat lze pouze šířku (a to pouze s krokem 160px), výška je následně dopočítána.

Před spuštění aplikace s onnx = True je potřeba prvně model vyexportovat pomocí export_onnx.py.

### Export onnx modelu
Pro úspěšný export modelu je potřeba zafixovat velikost vstupních obrázků. Defaultně aplikace využívá šířku 480px a 
výška je vydedukována z patřičné webkamery. Proto je potřeba prvně aplikaci spustit a v konzoli pozorovat velikosti 
obrázků do modelu vstupujících. 

Log aplikace pro detekci jednoho obrázku vypadá následovně:
```
Unmask detected!
384x480 1 unmasked_faces, Done inference. (0.844s)
Done full. (0.872s)
127.0.0.1 - - [10/Feb/2023 23:32:24] "POST /main/frame HTTP/1.1" 200 -
```
Zde je velikost obrázků patrná. V souboru export_onnx je potřeba patřičně nastavit konstantu IMAGE_SIZE a upravit i 
MODEL_NAME pro definici souboru exportovaného modelu. Tento soubor po exportu je nutné překopírovat do hlavního 
projektového adresáře. Následně stačí proceduru exportu spustit:
```
python export_onnx.py
```
Onnx runtime je konfigurovaný pouze na GPU z apoužití cuda, pokud takovými prostředky nedisponujete export skončí 
chybově.

## Spuštění
Pro spuštění aplikace:
```
python app.py
```
Aplikace je následně dostupná na: http://127.0.0.1:5000/. Je potřeba v prohlížeči povolit práva na použití webkamery. 
Následně je přenos z webkamery inicializován a na server jsou přeneseny informace o velikosti snímaných obrázků a je 
potřeba chvíli vyčkat než se model inicializuje. Poté kliknutím na tlačítko Start stream je zahájen přenos.

### Možné problémy
V případě chyby "ImportError: DLL load failed while importing _dlib_pybind11: The specified module could not be found" při spuštění aplikace 
je potřeba přeinstalovat dlib modul pomocí:
```
pip uninstall dlib
pip install dlib
```
Pokud tento proces nezabírá je možné ještě vyzkoušet nastavení cesty CUDA_PATH do __init__.py skriptu balíčku dlib jak je popsáno zde:
https://github.com/davisking/dlib/issues/2097. Pokud ani toto nezabere pak je pravděpodobné ž Váš procesor nepodporuje operace nutné pro kooperaci dlib a CUDA.

## Log
V menu aplikace po kliknutí na Log je možno pozorovat individuální osoby co byly ve streamu nalezeny bez masky. 
Tyto by měli obsahovat co nejméně duplicitních lidí, neboť jednotlivé obličeje jsou vůči sobě porobvnávány 
rozpoznáváním obličejů.

## Spuštění testovací procedury
Pro spuštění testovací procedury slouží příkaz:
```
python test.py --img-size 320 --device 0
```
Parametr img-size určuje scale velikost testovacích dat, síť scaluje data do čtvercových rozměrů a tedy stačí definovat pouze jednu velikost. 
Ne všechny velikosti vstupu jsou pro konfiguraci sítě validní, mezi možné hodnoty patří: 768, 704, 640, 576, 512, 448, 384, 320 a 256.
Parametr --device určuje zařízení použité pro výpočty sítě. Pro využití GPU a CUDA zadejte hodnotu '0' a pro CPU hodnotu 'cpu'.
# Ostatní větve

## feature/socketio
Tato větev obsahuje implementaci přenosu obrázků z klienta na server pomocí socketio jako pokus o optimalizaci procesu. 
Bohužel tento přenos je výrazně pomalejší než AJAX requesty.

## feature/webSocket
Tato větev implementuje technologii web socket pro přenos obrázků z klienta na server jako pokus o optimalizaci procesu.
Nativní js web-scoket a flask-sock je sice znatelně rychlejší než socketio, ale i tak na rychlost AJAX requestů 
nedosahuje.
