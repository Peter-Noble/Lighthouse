import pyspacemouse
import time
import threading


def watch_device(device):
    print(f"Starting thread with {device.name}")
    while True:
        print(device.read())
        # time.sleep(0.1)


def main():
    devices = pyspacemouse.open_all()

    if all([device for device in devices]):
        for device in devices:
            device.set_led(0)
        time.sleep(1)
        for device in devices:
            device.set_led(1)
        threads = [threading.Thread(target=watch_device, args=[device]) for device in devices]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()


if __name__ == "__main__":
    main()
