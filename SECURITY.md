# Security Policy

## Supported Versions

Мы поддерживаем следующие версии Legion Framework с security updates:

| Version | Supported          |
| ------- | ------------------ |
| 2.3.x   | :white_check_mark: |
| 2.2.x   | :white_check_mark: |
| 2.1.x   | :x:                |
| < 2.0   | :x:                |

## Reporting a Vulnerability

**НЕ создавайте публичные GitHub issues для security vulnerabilities.**

### Процесс сообщения

1. **Email**: Отправьте детали на legion14041981@gmail.com
2. **Включите**:
   - Описание уязвимости
   - Шаги для воспроизведения
   - Потенциальное влияние
   - Предлагаемое решение (если есть)

3. **Response Time**:
   - Подтверждение получения: в течение 48 часов
   - Первоначальная оценка: в течение 5 рабочих дней
   - Fix и disclosure: зависит от серьезности

### Severity Levels

- **Critical**: Немедленное исправление, emergency release
- **High**: Исправление в течение 7 дней
- **Medium**: Исправление в следующем minor release
- **Low**: Исправление в следующем major release

## Security Measures

### Implemented

- ✅ **Package Whitelist**: Валидация установки dependencies
- ✅ **Input Validation**: Проверка всех внешних данных
- ✅ **Subprocess Security**: Защита от injection attacks
- ✅ **Dependabot**: Автоматическое обновление зависимостей
- ✅ **Security Scanning**: Bandit, Safety, pip-audit в CI

### Planned

- 🔄 **Secret Scanning**: GitHub Secret Scanning
- 🔄 **CodeQL Analysis**: Advanced security analysis
- 🔄 **SBOM**: Software Bill of Materials generation
- 🔄 **Signed Releases**: GPG signing for releases

## Best Practices

### For Users

1. **Always use latest version**
2. **Review Dependabot PRs promptly**
3. **Use environment variables** for secrets
4. **Enable 2FA** on GitHub account
5. **Review security advisories** regularly

### For Contributors

1. **Never commit secrets** or credentials
2. **Use pre-commit hooks** for security checks
3. **Follow secure coding guidelines**
4. **Add tests** for security-related code
5. **Document security considerations**

## Security Checklist

Перед каждым release:

- [ ] Все dependencies обновлены
- [ ] Security scan пройден
- [ ] No known vulnerabilities
- [ ] Tests покрывают security scenarios
- [ ] Documentation обновлена
- [ ] CHANGELOG включает security fixes

## Disclosure Policy

### Coordinated Disclosure

1. **Private notification** для maintainers
2. **Fix development** в private branch
3. **Public disclosure** после fix release
4. **Credit** для reporter (если желает)

### Public Disclosure Timeline

- **Critical**: После emergency release
- **High**: 7 дней после fix release
- **Medium**: 14 дней после fix release
- **Low**: 30 дней после fix release

## Security Updates

Подпишитесь на security updates:

- **GitHub**: Watch repository → Custom → Security alerts
- **RSS**: Subscribe to [releases feed](https://github.com/legion14041981-ui/Legion/releases.atom)

## Hall of Fame

Мы благодарим security researchers, которые помогли улучшить Legion:

<!-- List will be populated as reports come in -->

## Contact

Для вопросов по security:
- Email: legion14041981@gmail.com
- PGP Key: [Available on request]

---

**Последнее обновление**: 2025-12-02
