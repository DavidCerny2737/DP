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

### Postup

```
# clone this repository
git clone https://github.com/DavidCerny2737/DP.git
cd DP

# virtual environment and dependency install
pythom -m venv venv
venv\Scripts\activate
pip install -r requirments.txt
```
Dále je potřeba nainstalovat pytorch. Aplikace byla vyvýjena a testována s verzí torch 1.11.0 za použití cuda 11.3 a cpu
verze pytorch 1.13.1. Nainstalujte si vlastní verzi pytorch podle nabídky instalací na:
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

## Log

V menu aplikace po kliknutí na Log je možno pozorovat individuální osoby co byly ve streamu nalezeny bez masky. 
Tyto by měli obsahovat co nejméně duplicitních lidí, neboť jednotlivé obličeje jsou vůči sobě porobvnávány 
rozpoznáváním obličejů.

# Ostatní větve

## feature/socketio
Tato větev obsahuje implementaci přenosu obrázků z klienta na server pomocí socketio jako pokus o optimalizaci procesu. 
Bohužel tento přenos je výrazně pomalejší než AJAX requesty.

## feature/webSocket
Tato větev implementuje technologii web socket pro přenos obrázků z klienta na server jako pokus o optimalizaci procesu.
Nativní js web-scoket a flask-sock je sice znatelně rychlejší než socketio, ale i tak na rychlost AJAX requestů 
nedosahuje.