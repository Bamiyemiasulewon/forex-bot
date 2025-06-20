class SubscriptionTier:
    FREE = 'free'
    PREMIUM = 'premium'
    VIP = 'vip'

# Determine the user's subscription tier from the user object.
def get_user_tier(user):
    # Placeholder: determine user tier from user object
    return SubscriptionTier.FREE

# Check if the user can receive a signal based on their tier and signals sent today.
def can_receive_signal(user, signals_sent_today):
    tier = get_user_tier(user)
    if tier == SubscriptionTier.FREE:
        return signals_sent_today < 3
    return True

# Get the list of features available for a given subscription tier.
def get_tier_features(tier):
    if tier == SubscriptionTier.FREE:
        return ['3 signals/day', 'basic updates', 'education']
    elif tier == SubscriptionTier.PREMIUM:
        return ['unlimited signals', 'priority alerts', 'advanced analysis']
    elif tier == SubscriptionTier.VIP:
        return ['all features', 'private group', 'video analysis']
    return [] 