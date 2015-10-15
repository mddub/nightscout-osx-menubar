# nightscout-osx-menubar

View CGM data from [Nightscout] in the OS X menu bar.

![nightscout-osx-menubar screenshot](https://raw.githubusercontent.com/mddub/nightscout-osx-menubar/master/screenshot.png)

## Requirements

* OS X (tested with 10.8 and 10.10, may work with earlier versions)
* A working installation of Nightscout ([cgm-remote-monitor])

## Installation

1. Download [this zip file containing the app][release-zip] and unzip it.
1. Drag "Nightscout Menubar" into your "Applications" folder.
1. Run it.

## Development

This uses [rumps], which provides a nice interface to PyObjC to create simple menu bar apps, and [py2app], a Python setuptools command which allows you to package Python scripts as standalone OS X applications.

To run the app in development:

```
git clone https://github.com/mddub/nightscout-osx-menubar
cd nightscout-osx-menubar
pip install -r requirements.txt --user  # This may take a while
python nightscout_osx_menubar.py
```

(We install requirements with `--user` because [rumps is not compatible with virtualenv][rumps-virtualenv]. You could alternatively `sudo pip install`.)

To package the app:

```
python setup.py py2app
```

## Troubleshooting

* If an error occurs while running the standalone app, some additional information was probably logged to the Console app (in Applications > Utilities).

* If you're running the app in development, you can get extra debug information from rumps by passing the `--debug` flag: `python nightscout_osx_menubar.py --debug`

## Notes

[File an issue] if you'd like to give feedback, request an enhancement, or report a bug. Pull requests are welcome.

## Disclaimer

This project is intended for educational and informational purposes only. It is not FDA approved and should not be used to make medical decisions. It is neither affiliated with nor endorsed by Dexcom.

[Nightscout]: http://www.nightscout.info/
[cgm-remote-monitor]: https://github.com/nightscout/cgm-remote-monitor
[release-zip]: https://github.com/mddub/nightscout-osx-menubar/raw/master/release/nightscout-osx-menubar.zip
[rumps]: https://github.com/jaredks/rumps
[py2app]: https://pythonhosted.org/py2app/
[rumps-virtualenv]: https://github.com/jaredks/rumps/issues/9
[File an issue]: https://github.com/mddub/nightscout-osx-menubar/issues
