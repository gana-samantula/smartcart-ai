/// Client-side checks that mirror the API's rules. The API still validates everything.
final RegExp _emailPattern = RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$');

const int passwordMinLength = 12;
const int passwordMaxLength = 128;

String? validateEmail(String? value) {
  final email = value?.trim() ?? '';
  if (email.isEmpty) {
    return 'Enter your email address.';
  }
  if (email.length > 320 || !_emailPattern.hasMatch(email)) {
    return 'Enter a valid email address.';
  }
  return null;
}

String? validateNewPassword(String? value) {
  final password = value ?? '';
  if (password.length < passwordMinLength) {
    return 'Use at least $passwordMinLength characters.';
  }
  if (password.length > passwordMaxLength) {
    return 'Use at most $passwordMaxLength characters.';
  }
  return null;
}

/// Existing passwords are not re-checked against the policy at sign-in, only for presence.
String? validateCurrentPassword(String? value) {
  if (value == null || value.isEmpty) {
    return 'Enter your password.';
  }
  return null;
}

/// Takes the original password as an argument, so the validator always compares against the
/// password as it is now, not as it was when the form was built.
String? validateConfirmation(String? value, String original) {
  return value == original ? null : 'Passwords do not match.';
}

String? validateRequired(String? value, String message) {
  if (value == null || value.trim().isEmpty) {
    return message;
  }
  return null;
}
