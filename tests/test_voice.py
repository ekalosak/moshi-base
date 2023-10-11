from moshi.voice import Voice

def test_init():
    _ = Voice(
        model='en-US-Wavenet-A',
        bcp47='en-US',
        language_name = 'English (United States)',
        gender = 1,
        type = 'Wavenet'
    )

def test_init_fast():
    _ = Voice('en-US-Wavenet-A', 2)
