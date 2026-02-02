# Скрипт для лёгкой установки и настройки ядра X-ray без графического интерфейса

Вы все знакомы с такими панелями управления, как 3x-ui, Marzban и другими. Все эти панели являются всего лишь графическими надстройками над ядром X-ray и служат для удобного управления им, а также для создания подключений и настроек. Ядро же может работать без всяких панелей и управляться полностью через терминал. Основное преимущество использования «голого» ядра заключается в том, что вам не нужно заморачиваться с доменами и TLS-сертификатами. Само ядро можно установить и администрировать вручную с помощью официальной документации. Этот скрипт предназначен для упрощения этой задачи: он автоматически установит ядро на сервер, создаст конфигурационные файлы и несколько исполняемых файлов для удобного управления пользователями.

## Системные требования

- 1 CPU  
- 1 GB RAM  
- 10 GB диска  


## Как пользоваться скриптом
Скрипт тестировался под ОС Ubuntu 22, 24, Debian 11. На других ОС может работать некорректно.  
Склонируйте репозиторий, перейдите в его корневую директорию и запустите скрипт установки с соответвующим 
протоколом, например:
```sh
git clone https://github.com/qmel/simple-xray-core.git
cd simple-xray-core
sudo ./xray-install vless-tcp
```
Добавьте пользователя, перезапустите сервис и выведите ссылку и QR-код для подключения:
```sh
xray-user -add username
sudo systemctl restart xray
xray-user -link username
```
Поддерживаемые протоколы
- `vless-tcp` (Vless TCP)
- `vless-xhttp` (Vless XHTTP)

**ВНИМАНИЕ!** При повторном запуске скрипта предыдущие ключи и пользователи будут удалены, их придется подключать заново.



## Команды для управления пользователями

**Вывести список всех клиентов:**

```sh
xray-user -show
```

**Создать нового пользователя:**

```sh
xray-user -add username
```

**Удалить пользователя:**

```sh
xray-user -rm username [-f]
```

**Вывести ссылку и QR-код для подключения пользователя:**

```sh
xray-user -link username
```

**Команда для перезагрузки ядра Xray**:

```sh
systemctl restart xray
```

**Файл конфигурации находится по адресу**:

```sh
/usr/local/etc/xray/config.json
```

## Проблемы с доступом по протоколу Vless на транспорте TCP.
> Многие заметили, что с доступностью Vless на транспорте TCP наблюдались некоторые проблемы. Я добавил вариацию этого скрипта с протоколом XHTTP. Важно! XHTTP - сравнительно новый транспорт, поэтому далеко не все клиенты его поддерживают. Список клиентов есть в текстовой версии видео на Github.
- [Ссылка на видео YouTube про XHTTP](https://youtu.be/XASBkzQE00s)
- [Текстовая версия видео на Github](https://github.com/ServerTechnologies/3x-ui-with-xhttp)

## Полезные ссылки

- [GitHub проекта X-ray Core](https://github.com/XTLS/Xray-core)
- [Официальная документация на русском](https://xtls.github.io/ru/)

## Клиенты для подключения

**Windows**

- [v2rayN](https://github.com/2dust/v2rayN)  
- [Furious](https://github.com/LorenEteval/Furious)  
- [Invisible Man - Xray](https://github.com/InvisibleManVPN/InvisibleMan-XRayClient)  

**Android**

- [v2rayNG](https://github.com/2dust/v2rayNG)  
- [X-flutter](https://github.com/XTLS/X-flutter)  
- [SaeedDev94/Xray](https://github.com/SaeedDev94/Xray)  

**iOS & macOS arm64**

- [Streisand](https://apps.apple.com/app/streisand/id6450534064)  
- [Happ](https://apps.apple.com/app/happ-proxy-utility/id6504287215)  
- [OneXray](https://github.com/OneXray/OneXray)  

**macOS arm64 & x64**

- [V2rayU](https://github.com/yanue/V2rayU)  
- [V2RayXS](https://github.com/tzmax/V2RayXS)  
- [Furious](https://github.com/LorenEteval/Furious)  
- [OneXray](https://github.com/OneXray/OneXray)  

**Linux**

- [Nekoray](https://github.com/MatsuriDayo/nekoray)  
- [v2rayA](https://github.com/v2rayA/v2rayA)  
- [Furious](https://github.com/LorenEteval/Furious)  

## Если вдруг нужно удалить, то воспользуйтесь этими командами:
```sh
bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ remove
rm /usr/local/etc/xray/config.json
rm /usr/local/etc/xray/.keys
rm /usr/local/etc/xray/.users.json
rm /usr/local/bin/xray-user
```
и удалите склонированный репозиторий
