class Settings:
    # APP SETTINGS
    # ///////////////////////////////////////////////////////////////
    ENABLE_CUSTOM_TITLE_BAR = True
    MENU_WIDTH = 240
    LEFT_BOX_WIDTH = 240
    RIGHT_BOX_WIDTH = 240
    TIME_ANIMATION = 500
    THREAD_REFERENCE = None

    VIDEO_PREDICTION = True
    AUDIO_PREDICTION = True
    TEXT_PREDICTION = True
    MICROPHONE_INDEX_AND_NAME = (-1, "Default")

    DESCRIPTION = \
        "Multimodal Emotion Detection helps thorough the process of interview to investigate the emotions of " \
        "of the candidate.\n" \
        "1. Home Button - Enable/Disable recording channels and add names for the candidate and interviewer\n" \
        "2. Start recording emotions\n" \
        "3. Review interviews and the emotions. Delete or export statistics\n" \
        "4. Exit application\n\n" \
        "Authors: Bălan Cristian, Hanganu Bogdan"

    # BTNS LEFT AND RIGHT BOX COLORS
    BTN_LEFT_BOX_COLOR = "background-color: rgb(44, 49, 58);"
    BTN_RIGHT_BOX_COLOR = "background-color: #ff79c6;"

    # MENU SELECTED STYLESHEET
    MENU_SELECTED_STYLESHEET = """border-left: 22px solid qlineargradient(spread:pad, x1:0.034, y1:0, x2:0.216, y2:0, 
    stop:0.499 rgba(255, 121, 198, 255), stop:0.5 rgba(85, 170, 255, 0)); background-color: rgb(40, 44, 52); """
