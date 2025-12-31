import 'package:flutter/foundation.dart';
import '../../domain/entities/user.dart';

enum AuthState { initial, loading, authenticated, unauthenticated, error }

class AuthViewModel extends ChangeNotifier {
  AuthState _state = AuthState.initial;
  User? _currentUser;
  String? _errorMessage;

  AuthState get state => _state;
  User? get currentUser => _currentUser;
  String? get errorMessage => _errorMessage;

  bool get isLoading => _state == AuthState.loading;
  bool get isAuthenticated => _state == AuthState.authenticated;
  bool get hasError => _state == AuthState.error;

  // Mock user for testing
  final User _mockUser = User(
    id: '1',
    email: 'test@example.com',
    phone: '1234567890',
    name: 'Test User',
  );

  AuthViewModel() {
    _checkAuthStatus();
  }

  Future<void> _checkAuthStatus() async {
    _state = AuthState.loading;
    notifyListeners();

    // Simulate checking auth status
    await Future.delayed(const Duration(seconds: 1));

    // For testing, start as unauthenticated
    _state = AuthState.unauthenticated;
    _currentUser = null;
    notifyListeners();
  }

  Future<void> signIn(String email, String password) async {
    _state = AuthState.loading;
    _errorMessage = null;
    notifyListeners();

    try {
      // Simulate API call
      await Future.delayed(const Duration(seconds: 1));

      // Mock authentication - accept any email/password
      _currentUser = _mockUser;
      _state = AuthState.authenticated;
      notifyListeners();
    } catch (e) {
      _state = AuthState.error;
      _errorMessage = e.toString();
      notifyListeners();
    }
  }

  Future<void> signUp(String email, String phone, String password) async {
    _state = AuthState.loading;
    _errorMessage = null;
    notifyListeners();

    try {
      // Simulate API call
      await Future.delayed(const Duration(seconds: 1));

      // Mock registration
      _currentUser = User(
        id: DateTime.now().millisecondsSinceEpoch.toString(),
        email: email,
        phone: phone,
        name: email.split('@')[0],
      );
      _state = AuthState.authenticated;
      notifyListeners();
    } catch (e) {
      _state = AuthState.error;
      _errorMessage = e.toString();
      notifyListeners();
    }
  }

  Future<void> signOut() async {
    _state = AuthState.loading;
    notifyListeners();

    try {
      // Simulate API call
      await Future.delayed(const Duration(milliseconds: 500));

      _currentUser = null;
      _state = AuthState.unauthenticated;
      notifyListeners();
    } catch (e) {
      _state = AuthState.error;
      _errorMessage = e.toString();
      notifyListeners();
    }
  }

  void clearError() {
    _errorMessage = null;
    if (_state == AuthState.error) {
      _state = _currentUser != null
          ? AuthState.authenticated
          : AuthState.unauthenticated;
      notifyListeners();
    }
  }
}
