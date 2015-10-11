# nightscout-osx-menubar

View CGM data from [Nightscout] in the OS X menu bar.

![nightscout-osx-menubar screenshot](https://raw.githubusercontent.com/mddub/nightscout-osx-menubar/master/screenshot.png)

## Requirements

* OS X
* A working installation of Nightscout ([cgm-remote-monitor])

## Installation

Using `pip` + `virtualenv`:

```
git clone https://github.com/mddub/nightscout-osx-menubar
cd nightscout-osx-menubar
virtualenv venv && . venv/bin/activate
pip install -r requirements.txt  # This may take a while
python nightscout_osx_menubar.py &
```

## Notes

This uses [rumps], which provides a nice interface to PyObjC to create OS X menu bar apps.

**TODO:** Use [py2app] to package as a standalone app.

[File an issue] if you'd like to give feedback, request an enhancement, or report a bug. Pull requests are welcome.

## Disclaimer

This project is intended for educational and informational purposes only. It is not FDA approved and should not be used to make medical decisions. It is neither affiliated with nor endorsed by Dexcom.

[Nightscout]: http://www.nightscout.info/
[cgm-remote-monitor]: https://github.com/nightscout/cgm-remote-monitor
[rumps]: https://github.com/jaredks/rumps
[py2app]: https://pythonhosted.org/py2app/
[File an issue]: https://github.com/mddub/nightscout-osx-menubar/issues
