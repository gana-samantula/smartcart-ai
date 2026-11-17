/// Tokens for one signed-in session. Stored only in platform secure storage.
class SessionTokens {
  const SessionTokens({required this.accessToken, required this.refreshToken});

  factory SessionTokens.fromJson(Map<String, dynamic> json) {
    return SessionTokens(
      accessToken: json['access_token'] as String,
      refreshToken: json['refresh_token'] as String,
    );
  }

  final String accessToken;
  final String refreshToken;
}

/// The signed-in user's profile, as returned by `GET /api/v1/users/me`.
class UserProfile {
  const UserProfile({required this.id, required this.email, this.displayName});

  factory UserProfile.fromJson(Map<String, dynamic> json) {
    return UserProfile(
      id: json['id'] as String,
      email: json['email'] as String,
      displayName: json['display_name'] as String?,
    );
  }

  final String id;
  final String email;
  final String? displayName;
}
