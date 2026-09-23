// Caminho relativo: src-tauri/src/comandos.rs
// Modelo da skill criar-app-tauri: a fronteira. Comando fino, validação na borda,
// trabalho pesado fora da thread principal, progresso por evento.
use std::sync::Mutex;

use serde::Serialize;
use tauri::{AppHandle, Emitter, State};

use crate::erro::ErroApp;

#[derive(Default)]
pub struct Projeto {
    pub nome: String,
    pub vaos: Vec<f64>,
}

#[derive(Serialize, Clone)]
pub struct Progresso {
    pub feito: usize,
    pub total: usize,
}

/// Comando síncrono e barato: valida, delega ao domínio, converte o erro.
#[tauri::command]
pub fn calcular_flecha(vao: f64, tracao: f64) -> Result<f64, ErroApp> {
    if !vao.is_finite() || vao <= 0.0 {
        return Err(ErroApp::Entrada("vão deve ser positivo e finito".into()));
    }
    if !tracao.is_finite() || tracao <= 0.0 {
        return Err(ErroApp::Entrada("tração deve ser positiva e finita".into()));
    }
    // A lógica mora no domínio, que não conhece o Tauri — é o que permite `cargo test`.
    crate::dominio::flecha(vao, tracao).map_err(|e| ErroApp::Interno(e.to_string()))
}

/// Estado compartilhado: Mutex bloqueante só em comando SÍNCRONO.
#[tauri::command]
pub fn renomear_projeto(nome: String, estado: State<'_, Mutex<Projeto>>) -> Result<(), ErroApp> {
    let nome = nome.trim();
    if nome.is_empty() || nome.len() > 120 {
        return Err(ErroApp::Entrada("nome entre 1 e 120 caracteres".into()));
    }
    estado
        .lock()
        .map_err(|_| ErroApp::Interno("estado envenenado".into()))?
        .nome = nome.to_owned();
    Ok(())
}

/// Trabalho longo: sai da thread principal e reporta progresso por evento.
/// Comando que demora e não faz isso é interface congelada.
#[tauri::command]
pub async fn processar_tudo(app: AppHandle, vaos: Vec<f64>) -> Result<usize, ErroApp> {
    if vaos.is_empty() {
        return Err(ErroApp::Entrada("nenhum vão informado".into()));
    }
    let total = vaos.len();
    tauri::async_runtime::spawn_blocking(move || {
        for (i, v) in vaos.iter().enumerate() {
            crate::dominio::processar(*v);
            let _ = app.emit("progresso", Progresso { feito: i + 1, total });
        }
        total
    })
    .await
    .map_err(|e| ErroApp::Interno(e.to_string()))
}
