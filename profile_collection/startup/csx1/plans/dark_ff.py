# dark and flatfield plans

import bluesky.plans as bp
import bluesky.plan_stubs as bps
from ..startup.optics import inout
from ..startup.detectors import fccd


def ct_dark(numim=None, detectors=None, gain_std=0):
    """Collect dark images for fccd and add metadata tag for dark and gain.

The pre-count shutter & gain states preserved.

    Parameters
    -----------
    numim: int

        Number of images to be measured. If different from current
        setting, the number of images will revert back to the original
        after the scan is complete.

    detectors: list
        List of detectors to be recorded.
        Default = [fccd]

    gain_std: int
        List of detectors to be recorded.
        Default = 0   (which is 'Auto' or x8, the most sensitive gain)

    Returns
    -------

    """
    if detectors is None:
        detectors = [fccd]
    print('starting dark')
    try:
        getit = inout.read()
        dark_shutter_state = getit['inout_status']['value']
        dark_sh_dict = {'Inserted': 'In', 'Not Inserted': 'Out'}
        gain_bit_dict = {0: 'auto', 1: 'x2', 2: 'x1'}

        # TODO figureout kwargs and self to mkae up to line 44 a
        # single definition
        getit = fccd.cam.read_configuration()
        print('read config')
        oldnumim = getit['fccd_cam_num_images']['value']
        acq_time = getit['fccd_cam_acquire_time']['value']
        acq_period =  getit['fccd_cam_acquire_period']['value']
        gain_state = getit['fccd_cam_fcric_gain']['value']
        print('got fccd staring params')
        # Printing info
        print(
            '\nStarting procedure to acquire darks '
            '{:3.3}Hz or {:3.3f}s.\n'.format(
                1/acq_time, acq_time))

        print('\tCurrent number of images = {}.\n'.format(oldnumim))

        yield from bps.sleep(.3) #TODO needed to make sure that the readback is changed im time for numim

        if numim is not None:
            print('\tSetting to {} images.\n'.format(numim))
            yield from bps.abs_set(fccd.cam.num_images, numim, wait=True)

        yield from bps.mv(inout, 'In')
        print('Beam blocked.')
        # This has to be 2 until we can selectively remove dark images
        # get_fastccd_images()  #TODO - fails here to _ct_dark
        yield from bps.sleep(acq_time*2.01)
        # SET TO 1 TO ARM FOR NEXT EVENT so that the FastCCD1 is
        # already bkg subt
        print('Correcting live image dark...')
        yield from bps.mv(fccd.fccd1.capture_bgnd, 1)
        yield from bps.sleep(0.3)
        print('Background updated.')
        # take darks
        yield from _ct_dark(detectors, gain_std, gain_bit_dict)

        # Putting things back
        yield from _ct_dark_cleanup(oldnumim, gain_bit_dict,
                                    gain_state, dark_sh_dict,
                                    dark_shutter_state, acq_time)
    except Exception:
        yield from _ct_dark_cleanup(oldnumim, gain_bit_dict, gain_state,
                                    dark_sh_dict, dark_shutter_state,acq_time)
        raise
    except KeyboardInterrupt:
        yield from _ct_dark_cleanup(oldnumim, gain_bit_dict,
                                    gain_state, dark_sh_dict,
                                    dark_shutter_state, acq_time)
        raise


def _ct_dark(detectors, gain_bit_input, gain_bit_dict):
    #adding because it gets  hung some where around here TODO
    print('Moving gains next.')
    yield from bps.sleep(1)
    yield from bps.mv(fccd.cam.fcric_gain, gain_bit_input)
    # if _gain_bit_input != 0:
    #     yield from bps.sleep(fccd.cam.acquire_period.value*2.01) # This has to be 2 until we can selectively remove dark images get_fastccd_images()
    print('\n\nGain bit set to {} for a gain value of {}\n'.format(
        gain_bit_input, gain_bit_dict.get(gain_bit_input)))

    #adding because it gets hung somewhere around here #TODO
    print('Ready to begin data collection next.')
    yield from bps.sleep(1)

    # TODO use remove this MD and add MD for plan_name
    yield from bp.count(detectors,
                        md={'fccd': {
                            'image': 'dark',
                            'gain': gain_bit_dict.get(gain_bit_input)}})

    # Commented this out because we should be using the md
    # olog('ScanNo {} Darks at for {}Hz or {}s with most sensitive gain

    # ({},Auto)'.format(db[-1].start['scan_id'],1/fccd.cam.acquire_time.value,fccd.cam.acquire_time.value,fccd.cam.fcric_gain.value))


def _ct_dark_cleanup(oldnumim, gain_bit_dict, gain_state,
                     dark_sh_dict, dark_shutter_state,acq_time):
    print('\nReturning to intial conditions (pre-count).')
    yield from bps.abs_set(fccd.cam.num_images, oldnumim, wait=True)

    yield from bps.mv(fccd.cam.fcric_gain, gain_state)
    yield from bps.mv(inout, dark_sh_dict.get(dark_shutter_state))
    yield from bps.sleep(acq_time*1)
    getit = fccd.cam.fcric_gain.read()
    gain_state_final = getit['fccd_cam_fcric_gain']['value']

    print('\tTotal images per trigger are NOW:\t {}'.format(
        fccd.cam.num_images.setpoint))
    print('\tFCCD FCRIC gain value is NOW:\t\t {}\n\n'.format(
        gain_bit_dict.get(gain_state_final)))


def ct_dark_all(numim=None, detectors=None):
    """Collect dark images for fccd and add metadata tag for dark and gain.

    The pre-count shutter & gain states preserved.

    Parameters
    -----------
    numim: int
        Number of images to be measured.

    detectors: list
        List of detectors to be recorded.
        Default = [fccd]

    Returns
    -----------

    """
    if detectors is None:
        detectors = [fccd]
    try:

        getit =  inout.read()
        dark_shutter_state = getit['inout_status']['value']
        dark_sh_dict = {'Inserted': 'In', 'Not Inserted': 'Out'}
        gain_bit_dict = {0: 'auto', 1: 'x2', 2: 'x1'}

        getit = fccd.cam.read_configuration()
        oldnumim = getit['fccd_cam_num_images']['value']
        acq_time = getit['fccd_cam_acquire_time']['value']
        acq_period =  getit['fccd_cam_acquire_period']['value']
        gain_state = getit['fccd_cam_fcric_gain']['value']

        # Printing info
        print('\nStarting procedure to acquire darks '
              '{:3.3}Hz or {:3.3f}s.\n'.format(
                  1/acq_time, acq_time))
        print('\tCurrent number of images = {}.\n'.format(oldnumim))

        yield from bps.sleep(.3)

        if numim is not None:
            print('\tSetting to {} images.\n'.format(numim))
            yield from bps.abs_set(fccd.cam.num_images, numim, wait=True)


        yield from bps.mv(inout, 'In')
        # This has to be 2 until we can selectively remove dark images
        # get_fastccd_images()
        yield from bps.sleep(acq_time*2.01)
        # SET TO 1 TO ARM FOR NEXT EVENT so that the FastCCD1 is
        # already bkg subt
        yield from bps.mv(fccd.fccd1.capture_bgnd, 1)

        # take darks
        for i in range(0, 3):
            gain_std = i
            yield from _ct_dark(detectors, gain_std, gain_bit_dict)

        # Putting things back
        yield from _ct_dark_cleanup(oldnumim, gain_bit_dict,
                                    gain_state, dark_sh_dict,
                                    dark_shutter_state,acq_time)

    except Exception:
        yield from _ct_dark_cleanup(oldnumim, gain_bit_dict,
                                    gain_state, dark_sh_dict,
                                    dark_shutter_state, acq_time)
        raise
    except KeyboardInterrupt:
        yield from _ct_dark_cleanup(oldnumim, gain_bit_dict, gain_state,
                                    dark_sh_dict, dark_shutter_state, acq_time)
        raise
