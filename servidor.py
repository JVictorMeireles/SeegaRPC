# from jogo_seega import JogoSeega
import Pyro5.api
import time
import json

@Pyro5.api.expose
class SeegaServidor:
  def __init__(self):
    self.estado_jogo = ' '
    self.jogadores = {}  # chave = jogador_id, valor = timestamp do último ping
    self.tempo_timeout = 3  # segundos para considerar um jogador inativo
    self.mensagem_a_enviar = None
    self.encerra_jogo,self.reiniciar,self.desistencia, self.desligar = False,False,False,False
    self.aceitar_encerrar,self.aceitar_reinicio= False, False
    self.pode_limpar_variaveis_de_controle = [False,False]
    self.reiniciando_jogo=False
      
  def get_mensagens_chat(self):
    return self.mensagem_a_enviar

  def enviar_estado(self, json_dados):
    dados=json.loads(json_dados)
    #Coleta a mensagem do chat, se houver
    if mensagem := dados.get('mensagem_chat'):
      # Adiciona a mensagem ao histórico de mensagens
      self.mensagem_a_enviar = mensagem
    self.estado_jogo = json_dados
    #Verifica se na mensagem enviada pelo cliente contém alguma variável para mudar
    if dados.get('encerra_jogo') == True: self.encerra_jogo = True
    if dados.get('desistencia') == True: self.desistencia = True
    if dados.get('reiniciar') == True: self.reiniciar = True
    if dados.get('desligar') == True: self.desligar = True
    if dados.get('aceita_encerrar') == True:self.aceitar_encerrar = True
    if dados.get('aceita_reiniciar') == True:self.aceitar_reinicio = True
    # if dados.get('reiniciando_jogo'):self.reiniciar_jogo(dados.get('reiniciando_jogo'))
      
  def get_reiniciando_jogo(self):
    return self.reiniciando_jogo
  
  def get_qtd_jogadores(self):
    agora = time.time()
    # Remove jogadores inativos
    ativos = {
      jid: t for jid, t in self.jogadores.items()
      if agora - t <= self.tempo_timeout
    }
    self.jogadores = ativos
    return len(self.jogadores)
      
  def jogadores_prontos(self):
    #Somente ao ter pelo menos 2 jogadores que vai liberar para executar
    #o restante do código nos clientes
    return self.get_qtd_jogadores() >= 2
  
  def get_lista_jogadores(self):
    return self.jogadores
      
  def limpar_variaveis_de_controle(self):
    self.encerra_jogo,self.reiniciar,self.desistencia,self.desligar = False,False,False,False
    self.aceitar_encerrar,self.aceitar_reinicio = None,None
    self.pode_limpar_variaveis_de_controle = [False,False]
    self.reiniciando_jogo=False
    print("Variáveis de controle limpas.")

  def ping(self, jogador_id):
    self.jogadores[jogador_id] = time.time()

  def pode_limpar_variaveis(self, cor_jogador):
    #Vai liberar para limpar variáveis caso os 2 jogadores tenham acessado as variáveis
    if cor_jogador == "Verde":
      self.pode_limpar_variaveis_de_controle[0] = True
    elif cor_jogador == "Roxo":
      self.pode_limpar_variaveis_de_controle[1] = True
    return all(self.pode_limpar_variaveis_de_controle)

  def receber_estado(self):
    #Entrega o estado do jogo que foi passado por mensagem_a_enviar
    return self.estado_jogo,self.encerra_jogo,self.reiniciar,self.desistencia,self.aceitar_encerrar,self.aceitar_reinicio, self.desligar
  
  def registrar_jogador(self):
    self.remove_jogadores_inativos()
    novo_id = len(self.jogadores) + 1
    self.jogadores[novo_id] = time.time()
    print(f"Jogador {novo_id} conectado.")
    return novo_id
  
  def reiniciar_jogo(self,cor_jogador):
    self.estado_jogo = ' '
    self.reiniciando_jogo=True
    if self.pode_limpar_variaveis(cor_jogador):
      self.limpar_variaveis_de_controle()
  
  def remove_jogadores_inativos(self):
    agora = time.time()
    self.jogadores = {
      jid: t for jid, t in self.jogadores.items()
      if agora - t <= self.tempo_timeout
    }
    if len(self.jogadores)==0:
      self.mensagem_a_enviar = None
      self.estado_jogo = ''
      self.limpar_variaveis_de_controle()

#Define a uri como uma uri fixa para que não precise informar ao cliente a todo momento qual a nova uri
servidor = SeegaServidor()
daemon = Pyro5.api.Daemon(port=5555)
uri = daemon.register(servidor, objectId="seega.servidor")
print(f"Servidor ativo. URI: {uri}")
daemon.requestLoop()