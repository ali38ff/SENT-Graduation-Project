class AppConfig {
  static const String serverBase = String.fromEnvironment(
    'SERVER_BASE',
    defaultValue: 'http://127.0.0.1:5000',
  );

  static const String streamUrl = String.fromEnvironment(
    'STREAM_URL',
    defaultValue: 'http://127.0.0.1:8080/?action=stream',
  );

  static String get loginUrl => '$serverBase/login';
  static String get notifyUrl => '$serverBase/notify';
  static String get clearUrl => '$serverBase/clear';
  static String get takePhotoUrl => '$serverBase/take_photo';
}
