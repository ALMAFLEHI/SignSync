enum SignMode { alphabet, number, bankingIntent }

extension SignModeLabel on SignMode {
  bool get isActiveForFinalModel => this == SignMode.bankingIntent;

  String get displayName {
    switch (this) {
      case SignMode.alphabet:
        return 'Alphabet Mode';
      case SignMode.number:
        return 'Number Mode';
      case SignMode.bankingIntent:
        return 'Banking Intent Mode';
    }
  }

  String get description {
    switch (this) {
      case SignMode.alphabet:
        return 'Historical mode unavailable with the final 40-class model';
      case SignMode.number:
        return 'Historical mode unavailable with the final 40-class model';
      case SignMode.bankingIntent:
        return 'Final 40 banking intents';
    }
  }
}
