from moshi.voice import Voice

def test_init():
    _ = Voice(
        name='en-US-Wavenet-A',
        # bcp47='en-US',
        # language_name = 'English (United States)',
        ssml_gender = 1,
        # type = 'Wavenet'
    )
