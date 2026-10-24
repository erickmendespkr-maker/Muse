# Muse — validação pt-BR e APK de teste

Branch de trabalho: `audit/security-ptbr`. A `main` não foi modificada.

## O que foi conferido no código

- `app/src/main/AndroidManifest.xml` referencia `@xml/locales_config`.
- `app/src/main/res/xml/locales_config.xml` declara `pt-BR` (tag BCP 47).
- Recursos de tradução ficam em `app/src/main/res/values-pt-rBR/` (qualificador Android).
- As chaves e placeholders dos três conjuntos principais foram comparados com os recursos de origem. Isso não substitui compilação nem teste de interface.

## Teste de tradução sem Android SDK

Execute na raiz do repositório:

```bash
python3 ci/script/check_ptbr_resources.py
```

O script verifica todos os `strings*.xml` em `values`, `values-en` e `values-pt-rBR`. Qualquer falha deve ser corrigida antes do APK.

## Gerar APK debug localmente (sem GitHub Actions)

Requisitos: JDK 21, Android SDK 36, Build Tools 36.0.0, NDK 27.0.12077973, CMake 3.22.1, Node.js 22, Python 3 e `patchelf` (Linux/WSL). A primeira compilação pode demorar; os pacotes nativos precisam ser baixados de fontes externas. A configuração equivalente está em `.github/workflows/ptbr-apk.yml`.

Linux/macOS:

```bash
python3 ci/script/check_ptbr_resources.py
(cd web && npm ci && npm run build)
bash tools/runtime-pack/build-runtime-pack.sh arm64
bash tools/python-pack/build-python-pack.sh arm64
chmod +x ./gradlew
./gradlew :app:assembleDebug -PnoUniversal -PreleaseSkipKeystoreCheck=true --stacktrace
```

Windows PowerShell:

```powershell
python ci/script/check_ptbr_resources.py
cd web
npm ci
npm run build
cd ..
# Prepare os runtimes Node/Python via WSL/Linux antes de compilar.
.\gradlew.bat :app:assembleDebug -PnoUniversal -PreleaseSkipKeystoreCheck=true --stacktrace
```

O Gradle pode exigir primeiro a compilação dos módulos auxiliares; siga os erros de dependências e tarefas que ele reportar. Verifique o resultado em `app/build/outputs/apk/debug/`. Como o projeto divide por ABI, para aparelhos ARM64 escolha o APK `arm64-v8a`. **Não instale arquivos de origem desconhecida sem revisar a assinatura e as permissões.**

## Teste do idioma no Android

1. Faça backup dos dados do Muse atual antes de trocar APKs; assinaturas diferentes podem impedir atualização direta.
2. Instale a versão debug em um aparelho de teste (Android 13+ para idioma por aplicativo).
3. Acesse Configurações do Android → Aplicativos → Muse → Idioma e procure **Português (Brasil)**.
4. Verifique telas de chat, ferramentas, aprovações, permissões, canais, voz e mensagens de erro.
5. Teste também Android 12 ou anterior com o idioma do sistema em português.
6. Não habilite SMS, acessibilidade, root, Shizuku ou integrações com contas reais antes da auditoria de segurança.

## Limitações e publicação

- Um APK debug **não** é uma versão final assinada.
- O `assembleRelease` requer keystore própria e versionamento explícito. Não use chave de depuração como assinatura de produção.
- Este documento não atesta que o APK compila nem que a tradução está visualmente completa.
- GitHub Actions não é necessário para o teste local; o workflow `ptbr-apk.yml` tenta compilar automaticamente na branch isolada quando há minutos de execução disponíveis.
- A compilação local requer os arquivos `muse-runtime-assets.zip`, `muse-python-assets.zip` e bibliotecas nativas ARM64; executar somente o Gradle pode produzir um APK sem esses recursos.
