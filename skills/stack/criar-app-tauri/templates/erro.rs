// Caminho relativo: src-tauri/src/erro.rs
// Modelo da skill criar-app-tauri: erro de comando serializável, sem vazar detalhe de sistema.
//
// `anyhow::Error` NÃO implementa Serialize — comando que o devolve não compila. Este tipo
// converte a causa interna (rica, para o log) numa mensagem enxuta (para a interface).
use serde::Serialize;

#[derive(Debug, Serialize)]
#[serde(tag = "tipo", content = "detalhe", rename_all = "snake_case")]
pub enum ErroApp {
    /// Entrada recusada na borda — a interface pode corrigir e tentar de novo.
    Entrada(String),
    /// Falha ao ler ou gravar o arquivo que o usuário escolheu.
    Arquivo(String),
    /// Qualquer outra: mensagem genérica na interface, causa completa no log.
    Interno(String),
}

impl std::fmt::Display for ErroApp {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ErroApp::Entrada(m) => write!(f, "entrada inválida: {m}"),
            ErroApp::Arquivo(m) => write!(f, "falha no arquivo: {m}"),
            ErroApp::Interno(_) => write!(f, "falha interna"),
        }
    }
}

impl From<std::io::Error> for ErroApp {
    fn from(e: std::io::Error) -> Self {
        // O caminho completo vai para o log, não para a interface.
        log::error!("io: {e}");
        ErroApp::Arquivo(match e.kind() {
            std::io::ErrorKind::NotFound => "arquivo não encontrado".into(),
            std::io::ErrorKind::PermissionDenied => "sem permissão para acessar o arquivo".into(),
            _ => "não foi possível acessar o arquivo".into(),
        })
    }
}
