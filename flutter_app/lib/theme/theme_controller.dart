import 'package:flutter/widgets.dart';

import 'app_theme_preference.dart';
import 'theme_preference_store.dart';

class ThemeController extends ChangeNotifier {
  ThemeController({
    required ThemePreferenceStore store,
    AppThemePreference initialPreference = AppThemePreference.system,
  }) : _store = store,
       _preference = initialPreference;

  final ThemePreferenceStore _store;
  AppThemePreference _preference;

  AppThemePreference get preference => _preference;

  Future<void> load() async {
    try {
      final storedPreference = await _store.read();
      if (_preference == storedPreference) {
        return;
      }
      _preference = storedPreference;
      notifyListeners();
    } on Object {
      // System mode remains the privacy-safe fallback if preference loading fails.
    }
  }

  Future<void> setPreference(AppThemePreference preference) async {
    if (_preference == preference) {
      return;
    }
    _preference = preference;
    notifyListeners();
    try {
      await _store.write(preference);
    } on Object {
      // The immediate theme change remains active for this process.
    }
  }
}

class ThemeControllerScope extends InheritedNotifier<ThemeController> {
  const ThemeControllerScope({
    super.key,
    required ThemeController controller,
    required super.child,
  }) : super(notifier: controller);

  static ThemeController of(BuildContext context) {
    final scope = context
        .dependOnInheritedWidgetOfExactType<ThemeControllerScope>();
    assert(scope != null, 'ThemeControllerScope was not found.');
    return scope!.notifier!;
  }

  static ThemeController? maybeOf(BuildContext context) {
    return context
        .dependOnInheritedWidgetOfExactType<ThemeControllerScope>()
        ?.notifier;
  }
}
