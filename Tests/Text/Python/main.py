from TextEmotionPredictor import TextEmotionPredictor

# OCEAN (for openness, conscientiousness, extraversion, agreeableness, and neuroticism)

# Big Five Most widely used model for personality is Big Five Reconfirmed many times with Factor Analysis
#
# Extraversion (sociable vs shy): Energetic, active, assertive, outgoing, amicable, assertive. Friendly and
# energetic, extroverts draw inspiration from social situations.
#
# Neuroticism (neurotic vs calm): Anxious, tense, self-pitying, insecure, sensitive. Neurotics are anxious, moody,
# tense, and easily tipped into experiencing negative emotions.
#
# Agreeableness (friendly vs uncooperative): Compassionate, cooperative, cooperative, helpful, nurturing. People who
# score high in agreeableness are peace-keepers who are generally optimistic and trusting of others.
#
# Conscientiousness (organized vs careless): Efficient, organized, responsible, organized, and persevering.
# Conscientious individuals are extremely reliable and tend to be high achievers, hard workers, and planners.
#
# Openness (insightful vs unimaginative): Artistic, curious, imaginative, curious, intelligent, and imaginative. High
# scorers tend to be artistic and sophisticated in taste and appreciate diverse views, ideas, and experiences.


labels = ['Extraversion', 'Neuroticism', 'Agreeableness', 'Conscientiousness', 'Openness']


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    text = "Dearest, I feel certain that I am going mad again. I feel we can't go through another of those terrible " \
           "times. And I shan't recover this time. I begin to hear voices, and I can't concentrate. So I am doing " \
           "what seems the best thing to do. You have given me the greatest possible happiness. You have been in " \
           "every way all that anyone could be. I don't think two people could have been happier 'til this terrible " \
           "disease came. I can't fight any longer. I know that I am spoiling your life, that without me you could " \
           "work. And you will I know. You see I can't even write this properly. I can't read. What I want to say is " \
           "I owe all the happiness of my life to you. You have been entirely patient with me and incredibly good. I " \
           "want to say that – everybody knows it. If anybody could have saved me it would have been you. Everything " \
           "has gone from me but the certainty of your goodness. I can't go on spoiling your life any longer. I don't "\
           "think two people could have been happier than we have been. V. "
    textEmotionPredictor = TextEmotionPredictor()
    predictions = textEmotionPredictor.run(text, model_name="Personality_traits_NN")
    print(predictions)
