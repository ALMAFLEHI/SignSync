import 'package:shared_preferences/shared_preferences.dart';

import 'app_theme_preference.dart';

abstract interface class ThemePreferenceStore {
  Future<AppThemePreference> read();

  Future<void> write(AppThemePreference preference);
}

class SharedPreferencesThemePreferenceStore implements ThemePreferenceStore {
  static const String preferenceKey = 'signsync_theme_mode';

  @override
  Future<AppThemePreference> read() async {
    final preferences = await SharedPreferences.getInstance();
    return AppThemePreference.fromStorage(preferences.getString(preferenceKey));
  }

  @override
  Future<void> write(AppThemePreference preference) async {
    final preferences = await SharedPreferences.getInstance();
    await preferences.setString(preferenceKey, preference.storageValue);
  }
}
