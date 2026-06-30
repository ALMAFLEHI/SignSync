enum SignMode { normal, number }

extension SignModeLabel on SignMode {
  String get displayName {
    switch (this) {
      case SignMode.normal:
        return 'Normal Mode';
      case SignMode.number:
        return 'Number Mode';
    }
  }

  String get description {
    switch (this) {
      case SignMode.normal:
        return 'A-Z and banking intents';
      case SignMode.number:
        return 'Digits 0-9 only';
    }
  }
}
