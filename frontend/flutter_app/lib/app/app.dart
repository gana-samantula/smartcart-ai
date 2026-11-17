import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:material_ui/material_ui.dart';
import 'package:smartcart_app/app/router.dart';
import 'package:smartcart_app/app/theme.dart';

/// Root widget. Routing and theme are supplied by providers, so tests can swap them.
class SmartCartApp extends ConsumerWidget {
  const SmartCartApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return MaterialApp.router(
      title: 'SmartCart AI',
      theme: AppTheme.light(),
      routerConfig: ref.watch(routerProvider),
      debugShowCheckedModeBanner: false,
    );
  }
}
