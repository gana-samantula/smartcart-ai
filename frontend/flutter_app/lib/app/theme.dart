import 'package:material_ui/material_ui.dart';

/// Central theme definitions. Colors come from one seed so light and dark stay consistent.
abstract final class AppTheme {
  static const Color _seed = Color(0xFF1B7F5B);

  static ThemeData light() {
    return ThemeData(
      colorScheme: ColorScheme.fromSeed(seedColor: _seed),
      useMaterial3: true,
    );
  }
}
