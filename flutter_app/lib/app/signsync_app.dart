import 'dart:async';

import 'package:flutter/material.dart';

import '../config/app_config.dart';
import '../theme/signsync_theme.dart';
import '../theme/theme_controller.dart';
import '../theme/theme_preference_store.dart';
import '../ui/home_page.dart';

class SignSyncApp extends StatefulWidget {
  const SignSyncApp({super.key, this.themeController});

  final ThemeController? themeController;

  @override
  State<SignSyncApp> createState() => _SignSyncAppState();
}

class _SignSyncAppState extends State<SignSyncApp> {
  late final ThemeController _themeController;
  late final bool _ownsThemeController;

  @override
  void initState() {
    super.initState();
    _ownsThemeController = widget.themeController == null;
    _themeController =
        widget.themeController ??
        ThemeController(store: SharedPreferencesThemePreferenceStore());
    unawaited(_themeController.load());
  }

  @override
  void dispose() {
    if (_ownsThemeController) {
      _themeController.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ThemeControllerScope(
      controller: _themeController,
      child: AnimatedBuilder(
        animation: _themeController,
        builder: (context, _) => MaterialApp(
          title: AppConfig.appTitle,
          debugShowCheckedModeBanner: false,
          theme: SignSyncTheme.light,
          darkTheme: SignSyncTheme.dark,
          themeMode: _themeController.preference.themeMode,
          home: const HomePage(),
        ),
      ),
    );
  }
}
