class User {
  final String id;
  final String email;
  final String? phone;
  final String name;

  User({required this.id, required this.email, this.phone, required this.name});

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'],
      email: json['email'],
      phone: json['phone'],
      name: json['name'],
    );
  }

  Map<String, dynamic> toJson() {
    return {'id': id, 'email': email, 'phone': phone, 'name': name};
  }
}
