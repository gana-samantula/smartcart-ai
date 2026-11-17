/// Base URL of the SmartCart API. Override per build with:
///   flutter run --dart-define=SMARTCART_API_URL=http://10.0.2.2:8000
/// Android emulators reach the host machine at 10.0.2.2, not 127.0.0.1.
const String apiBaseUrl = String.fromEnvironment(
  'SMARTCART_API_URL',
  defaultValue: 'http://127.0.0.1:8000',
);
