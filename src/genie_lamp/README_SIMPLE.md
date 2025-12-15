# Genie-Lamp - No rm2fb Fork

Gesture detection without rm2fb dependency.

## Build

```bash
cd src/genie_lamp
./build.sh
```

## Deploy

```bash
scp ../../resources/rmkit/src/build/genie_lamp root@10.11.99.1:/opt/bin/
scp lamp_test.conf root@10.11.99.1:/opt/etc/genie_lamp.conf
```

## Run

```bash
ssh root@10.11.99.1 /opt/bin/genie_lamp /opt/etc/genie_lamp.conf
```

## Test

3-finger tap → draws square

## Requirements

- ARM cross-compiler: `sudo apt install g++-arm-linux-gnueabihf`
- okp: Already installed

## Notes

- No rm2fb needed
- Uses fixed 1404x1872 screen size
- 7 test gestures in lamp_test.conf
