# NetAutomationSwitches

## Origem do projeto

Este projeto nasceu da necessidade de gerenciar de forma centralizada um parque de switches de rede com múltiplos fabricantes. A equipe de infraestrutura enfrentava dificuldades para acompanhar o estado das portas manualmente, o que tornava lento o processo de identificar equipamentos ociosos, rastrear mudanças de configuração e gerar evidências para revisões periódicas.

A solução precisava atender três demandas principais:

**Conexões simultâneas** — a ferramenta deve ser capaz de conectar-se a vários switches ao mesmo tempo, sem travar a interface. Cada conexão SSH roda em uma thread separada (até 6 conexões em paralelo), com detecção automática de fabricante e coleta imediata de status de portas, CPU e memória.

**Relatórios de portas com pouco tempo de uso** — o sistema extrai o estado atual de cada porta (UP/DOWN) por switch e permite identificar portas que permanecem inativas, auxiliando na tomada de decisão sobre realocação ou desativação de recursos.

**Revisão periódica a cada 45 dias** — a cada 45 dias, o time deve revisar se as portas que foram alteradas (mudanças de estado, descrição ou VLAN) desde o dia da mudança até o momento atual sofreram alguma variação. Essa revisão garante que alterações realizadas em campo foram devidamente registradas e que nenhuma porta ficou em estado inconsistente sem acompanhamento.

## O que foi construído

O sistema é uma aplicação desktop e web desenvolvida em Python com o framework Flet. Ele se conecta a switches de rede via SSH utilizando a biblioteca Netmiko, com suporte a múltiplos fabricantes: Cisco, Huawei, HP/HPE, Aruba, Dell, Juniper e Arista.

A aplicação é composta pelas seguintes partes:

- Tela de login com autenticação via LDAP
- Página de dispositivos para adicionar switches a uma fila e conectar todos de uma vez ou individualmente
- Conector SSH com autodetecção de fabricante, probe TCP rápido para falha antecipada, e coleta de versão de firmware, modelo, portas UP/DOWN, uso de CPU e memória
- Dashboard com cards arrastáveis e redimensionáveis exibindo os dados de cada switch conectado em tempo real
- Gerenciamento de estado global dos switches conectados com propagação de atualizações para todos os componentes da interface
- Suporte a temas claro e escuro com atualização dinâmica

## Como executar

### Com uv

Como aplicação desktop:

```bash
uv run flet run
```

Como aplicação web:

```bash
uv run flet run --web
```

Para mais detalhes, consulte o [Guia de Início Rápido do Flet](https://docs.flet.dev/).

## Como compilar

### Android

```bash
flet build apk -v
```

Consulte o [Guia de Empacotamento Android](https://docs.flet.dev/publish/android/).

### iOS

```bash
flet build ipa -v
```

Consulte o [Guia de Empacotamento iOS](https://docs.flet.dev/publish/ios/).

### macOS

```bash
flet build macos -v
```

Consulte o [Guia de Empacotamento macOS](https://docs.flet.dev/publish/macos/).

### Linux

```bash
flet build linux -v
```

Consulte o [Guia de Empacotamento Linux](https://docs.flet.dev/publish/linux/).

### Windows

```bash
flet build windows -v
```

Consulte o [Guia de Empacotamento Windows](https://docs.flet.dev/publish/windows/).

### Web

```bash
flet build web -v
```

Consulte o [Guia de Empacotamento Web](https://docs.flet.dev/publish/web/).
