"""Generate lhcv.pdf in the student's Deadlock/Sync report format."""
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer, Table, TableStyle,
)

root = Path(__file__).resolve().parents[1]
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyReport', fontName='Helvetica', fontSize=10,
                         leading=14, spaceAfter=8))
styles.add(ParagraphStyle(name='CellReport', fontName='Helvetica', fontSize=8.5,
                         leading=11))
styles.add(ParagraphStyle(name='MonoReport', fontName='Courier', fontSize=8,
                         leading=11, spaceAfter=8))
styles['Heading2'].fontSize = 12
styles['Heading2'].spaceBefore = 10
styles['Heading2'].spaceAfter = 7
styles['Heading1'].fontSize = 15
styles['Heading1'].leading = 19
story = []


def p(text):
    story.append(Paragraph(text, styles['BodyReport']))


def h(text):
    story.append(Paragraph(text, styles['Heading2']))


def code(text):
    story.append(Preformatted(text, styles['MonoReport']))


def table(rows, widths, header=True):
    cells = [[Paragraph(escape(str(cell)).replace('\n', '<br/>'), styles['CellReport'])
              for cell in row] for row in rows]
    result = Table(cells, colWidths=widths, repeatRows=1 if header else 0, hAlign='LEFT')
    commands = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LINEBELOW', (0, 0), (-1, -1), 0.3, colors.HexColor('#d5d5d5')),
    ]
    if header:
        commands.append(('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e9e9e9')))
    else:
        commands.append(('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#eeeeee')))
    result.setStyle(TableStyle(commands))
    story.extend([result, Spacer(1, 8)])


def page():
    story.append(PageBreak())


story.append(Paragraph('Relatório - Implementação 7: Memória Virtual', styles['Heading1']))
table([
    ['Aluno', 'Luiz Henrique Carvalho Vieira'],
    ['Professor', 'Marcelo Lima Arcoverde'],
    ['Turma', '3º período B'],
    ['Disciplina', 'Infraestrutura de software'],
    ['Login', 'lhcv'],
    ['Repositório', 'github.com/luizvieiraa/Virtual-Memory'],
], [105, 402], False)
h('1. Objetivo')
p('Desenvolver em C um simulador de memória virtual com 128 frames, tabela de páginas e TLB de 16 entradas. Traduzir endereços lógicos de 16 bits, carregar páginas de BACKING_STORE.bin, aplicar FIFO ou LRU separadamente para páginas e TLB e gerar correct.txt. A consulta à TLB utiliza uma thread POSIX por entrada.')
h('2. Checklist de Requisitos')
table([
    ['Requisito', 'Status', 'Como testar / evidência'],
    ['Compilar com make e gerar vm', 'OK', 'Build e execução no Ubuntu/WSL e Windows/GCC.'],
    ['128 frames preenchidos de 0 a 127', 'OK', 'Modelo independente e casos de substituição.'],
    ['Traduzir página e deslocamento', 'OK', 'Limites 0 e 65535; bytes sintéticos com sinal.'],
    ['FIFO e LRU de páginas', 'OK', 'Recência, reuso e invalidação verificados.'],
    ['FIFO e LRU da TLB, independentes', 'OK', 'Quatro combinações comparadas integralmente.'],
    ['Uma thread por entrada da TLB', 'OK', '16 pthreads; join antes de alterar as estruturas.'],
    ['Ler endereços e tratar erros', 'OK', 'Argumentos, formatos, arquivos e saída no log.'],
    ['Gerar correct.txt no formato pedido', 'OK¹', '1000 índices e traduções iguais ao gabarito.'],
    ['Makefile com limpeza', 'OK', 'make clean confirmado no pacote extraído.'],
    ['README, evidências, PDF e TAR', 'OK', 'Arquivos presentes; conteúdo do TAR conferido.'],
], [228, 42, 237])
p('¹ A comparação com o gabarito excluiu os valores dos bytes: o BACKING_STORE.bin original não estava disponível. Os bytes foram validados com dados sintéticos. O PDF do enunciado traz Implementação 6 no cabeçalho; esta entrega segue a identificação 7 - VM do Classroom.')

page()
h('3. Como Reproduzir')
p('Ambiente exigido: Linux, Unix ou macOS, com compilador C11, POSIX threads e Make. A execução foi validada em Ubuntu via WSL2, GCC 15.2.0, e em Windows com MinGW-w64. Python 3 é necessário apenas para testes e empacotamento; não é necessário para compilar vm.')
p('Na raiz deste repositório, onde estão vm.c e Makefile:')
code('make clean\nmake\n./vm addresses.txt lru fifo\necho $?\ncat correct.txt')
p('O segundo argumento define a política de páginas e o terceiro a política da TLB. Ambos aceitam fifo ou lru em minúsculas. Colocar BACKING_STORE.bin no diretório de execução. A entrada contém um inteiro decimal de 0 a 65535 por linha. Espaços nas extremidades são aceitos; linhas vazias e arquivos vazios são rejeitados.')
p('Retorno esperado: 0. A execução normal grava correct.txt sem mensagens em stdout. Erros são apresentados em stderr e retornam falha. Guardar o gabarito com outro nome, pois correct.txt é sobrescrito. No PowerShell, usar $LASTEXITCODE para consultar o retorno numérico.')
code('make test\nmake package\ntar -xf lhcv.tar\ncd lhcv\nmake clean\nmake')
p('Os dois últimos comandos validam a pasta extraída. Os alvos opcionais test e package pertencem ao repositório completo; o TAR contém somente o fonte e o Makefile. Ao alternar Windows e WSL na mesma pasta, limpar ou forçar a recompilação para evitar reutilizar um executável do outro sistema.')
h('4. Arquitetura (resumida)')
table([
    ['Arquivo', 'Responsabilidade'],
    ['vm.c', 'Parser, estruturas, substituição, threads, tradução, saída e main.'],
    ['Makefile', 'Gera vm com -pthread; clean, test e package.'],
    ['tests/test_vm.py', 'Modelo independente, suíte sintética e comparação opcional.'],
    ['evidencias.log', 'Comandos, resultados e limitações das verificações.'],
    ['scripts/package.py', 'Gera lhcv.tar com lhcv/vm.c e lhcv/Makefile.'],
    ['scripts/report.py', 'Gera este PDF com ReportLab; não participa do build em C.'],
], [135, 372])

page()
h('5. Estratégias e Diário de Desenvolvimento')
h('5.1 Estratégias utilizadas')
table([
    ['Estratégia', 'Contexto', 'Motivo da evolução'],
    ['S1 - Base e entrada', 'Makefile, decomposição e parser', 'Validar o formato antes de simular memória.'],
    ['S2 - Memória física', '256 frames; depois 128, FIFO e LRU', 'Validar carga e substituição por etapas.'],
    ['S3 - TLB sequencial', 'FIFO/LRU e estatísticas', 'Conferir mapeamentos antes das threads.'],
    ['S4 - Busca paralela', '16 tarefas com cópias das entradas', 'Atender à concorrência sem escritas compartilhadas.'],
    ['S5 - Entrega', 'Testes, relatório e pacote', 'Verificar a reprodução fora do checkout.'],
], [127, 190, 190])
h('5.2 Diário de tentativas')
table([
    ['Tentativa', 'Resultado', 'Causa / evidência'],
    ['Preparar build e leitura de endereços', 'OK', 'a0c3937 e d1e45dc; 18/11.'],
    ['Carregar páginas com 256 frames', 'OK', 'c81bda5; 19/11.'],
    ['Reduzir para 128 e adicionar FIFO', 'OK', 'ba3e90b; 19/11.'],
    ['Adicionar LRU de páginas', 'OK', '4a8a8c3; 22/11.'],
    ['Integrar TLB e correct.txt', 'Parcial¹', 'bd3fa5f; 22/11; referência sem os bytes.'],
    ['Usar uma thread por entrada', 'OK', 'bf1f192; 23/11; saída igual à versão sequencial.'],
    ['Simular falha na sexta criação', 'Erro esperado', 'As cinco threads iniciadas foram aguardadas.'],
    ['Alternar build Linux/Windows', 'Falha de ambiente', 'Build existente impediu gerar vm.exe; recompilar com -B resolveu.'],
    ['Gerar e validar a entrega', 'OK', '6f6be4f; 23/11; suíte no TAR extraído.'],
], [222, 72, 213])
p('O diário descreve as etapas e os resultados registrados no histórico e no evidencias.log. Não foi documentado um bug funcional com captura antes/depois nesta implementação. A falha de ambiente acima foi de compilação entre sistemas, sem alteração do algoritmo. ¹ A limitação dos bytes está descrita na seção 6.2.')
h('5.3 Núcleo do algoritmo')
p('A consulta usa página = endereço / 256 e deslocamento = endereço % 256. Em miss da TLB, consulta a tabela; em page fault, lê 256 bytes na posição página × 256. Calcula frame × 256 + deslocamento e converte o byte para -128..127. A busca cria 16 threads por acesso; o custo de criação e junção pode superar o de uma busca sequencial tão curta. Não foi medida aceleração.')

page()
h('6. Evidências')
h('6.1 Log de testes e execução')
p('A suíte reproduzível usa um binário sintético com conteúdo conhecido e um modelo independente em Python. São 1.691 endereços por combinação de políticas, totalizando 6.764 por ambiente. O mesmo conjunto passou no Linux e no Windows. Para cada execução são comparadas todas as traduções, os valores e as cinco linhas de estatísticas.')
table([
    ['Verificação', 'Comando / método', 'Resultado'],
    ['Compilação Linux', 'make clean; make', 'Sem avisos; gera vm com -pthread.'],
    ['Compilação Windows', 'mingw32-make -B CC=gcc', 'Sem avisos; gera vm.exe.'],
    ['Quatro políticas', 'python3 tests/test_vm.py', 'Todos os casos sintéticos coincidiram.'],
    ['Entradas e arquivos inválidos', 'Suíte de erros e formato', 'Falha com diagnóstico; sem estatísticas de sucesso.'],
    ['Referência lru / fifo', '1000 endereços fornecidos', 'Índices, endereços e contadores iguais.'],
    ['Helgrind: caso curto', '0, 0, 65535; lru / fifo', '0 erros não suprimidos.'],
    ['Memcheck: caso curto', 'Mesmos três endereços', '0 erros e 0 bytes em uso ao encerrar.'],
    ['Pacote extraído', 'make; suíte; make clean', 'Conteúdo exato e execução confirmados.'],
], [120, 220, 167])
h('6.2 Saída observada e limites da referência')
code('PASS professor reference: all mappings, TLB indices and statistics;\n     byte values excluded\nNumber of Translated Addresses = 1000\nPage Faults = 539\nPage Fault Rate = 0.539\nTLB Hits = 54\nTLB Hit Rate = 0.054')
p('Transcrição do log, com a mensagem longa quebrada para leitura. A execução usou os endereços do professor e um backing store zerado. Apenas o campo Value foi excluído da comparação. Os 1.000 endereços físicos e índices da TLB, além das cinco estatísticas, coincidiram. Isso não valida o conteúdo do binário original.')
p('A cobertura de Helgrind e Memcheck foi de um caso curto. O Helgrind registrou 65 ocorrências suprimidas em três contextos; não houve erro não suprimido. Esses resultados não demonstram todas as intercalações possíveis das threads.')

page()
h('6.3 Casos de substituição e concorrência')
p('Os casos abaixo verificam as diferenças entre FIFO e LRU e a consistência das traduções. São cenários sintéticos do desenvolvimento e da suíte, não capturas de uma falha funcional observada.')
table([
    ['Cenário', 'Comportamento esperado / verificado'],
    ['Páginas 0..127; reacessar 0; carregar 128', 'FIFO remove a página 0. LRU protege 0 e remove 1.'],
    ['TLB com páginas 0..15; acessar 0; inserir 16', 'FIFO mantém a ordem de inserção; LRU protege a entrada recém-acessada.'],
    ['Miss da TLB com página residente', 'Reinserir tradução sem novo page fault.'],
    ['Remover página ainda presente na TLB', 'Invalidar a entrada antiga antes de traduzir novo acesso.'],
    ['Hit na TLB com LRU de páginas', 'Atualizar também a recência da página na memória física.'],
    ['Falha ao criar a sexta thread', 'Aguardar as cinco iniciadas; retornar erro. Verificação da etapa 7.'],
], [200, 307])
p('<b>Decisão de sincronização:</b> cada tarefa recebe uma cópia da entrada da TLB e escreve somente no próprio resultado. A principal chama pthread_join para todas as tarefas iniciadas antes de usar os resultados ou alterar a TLB. Assim, inserção, invalidação e atualização de recência ficam sequenciais, fora da consulta paralela.')
h('Histórico de commits verificado')
table([
    ['Commit', 'Descrição'],
    ['a0c3937', 'Etapa 1: criar build e decompor endereços lógicos.'],
    ['d1e45dc', 'Etapa 2: validar argumentos e ler endereços.'],
    ['c81bda5', 'Etapa 3: tabela de páginas e backing store.'],
    ['ba3e90b', 'Etapa 4: 128 frames e FIFO.'],
    ['4a8a8c3', 'Etapa 5: LRU de páginas.'],
    ['bd3fa5f', 'Etapa 6: TLB FIFO/LRU e correct.txt.'],
    ['bf1f192', 'Etapa 7: uma thread por entrada da TLB.'],
    ['6f6be4f', 'Etapa 8: documentação, validação e entrega.'],
], [80, 427])
p('As versões intermediárias da rubrica estão preservadas nesses commits. A versão final usa 128 frames e threads; não foi adicionada uma opção de execução para voltar às versões antigas.')

page()
h('7. Uso de IA')
p('Utilizei IA generativa para interpretar o enunciado, dividir o desenvolvimento em etapas, implementar e revisar o código em C, preparar Makefile e testes, comparar saídas e organizar README, evidências e relatório. Também solicitei à ferramenta a execução dos comandos no computador e a criação de um commit por etapa.')
p('Prompts principais, resumidos a partir da conversa:')
table([
    ['#', 'Solicitação'],
    ['1', 'Analisar a implementação e dividir o desenvolvimento em etapas.'],
    ['2', 'Conectar ao repositório e implementar as etapas 1 e 2 com um commit para cada.'],
    ['3', 'Continuar as etapas 3, 4 e 5: tabela de páginas, FIFO e LRU.'],
    ['4', 'Implementar a etapa 6: TLB e arquivo de saída.'],
    ['5', 'Implementar a etapa 7 com uma thread por entrada.'],
    ['6', 'Concluir a etapa 8 e gerar a documentação e o pacote de entrega.'],
    ['7', 'Refazer o relatório no padrão dos PDFs anteriores de Deadlock e Sync.'],
], [30, 477])
p('<b>Validação realizada:</b> a compilação, os testes, a comparação com o gabarito e a extração do TAR foram executados pelo assistente e registrados no log. A revisão manual independente do aluno não está registrada nas evidências disponíveis.')
h('8. Reflexão Final')
p('A tradução correta depende de manter coerentes a TLB, a tabela de páginas e a ocupação dos frames. Um mapeamento antigo na TLB pode apontar para um frame que já pertence a outra página. Por isso, a invalidação acompanha a substituição. Outra distinção é que o LRU da memória física precisa registrar o uso mesmo quando a tabela de páginas é evitada por um hit na TLB.')
p('A separação entre uma versão sequencial e uma versão com threads permitiu comparar o resultado antes e depois da paralelização. As cópias das entradas e os resultados separados simplificam a consistência, mas criar 16 threads por endereço possui custo. A validação também mostrou a importância de distinguir os campos conferidos no gabarito dos bytes que ainda dependem do arquivo original.')
h('9. Checklist Final de Entrega')
table([
    ['Item', 'Situação'],
    ['Compilar do zero e testar no Linux', 'Confirmado no Ubuntu/WSL.'],
    ['Testar limites, erros e quatro políticas', 'Confirmado; evidencias.log.'],
    ['Conferir pacote extraído e limpeza', 'Confirmado; dois arquivos no TAR.'],
    ['Preencher uso de IA e revisar o relatório', 'Preenchido no modelo anterior.'],
    ['Comparar todos os bytes com o material original', 'Pendente: falta BACKING_STORE.bin.'],
    ['Enviar ao Classroom e publicar os commits', 'Não realizado pelo assistente.'],
], [340, 167])

page()
h('10. Se eu tivesse mais 2 horas')
p('A primeira prioridade seria obter o BACKING_STORE.bin original e executar a comparação completa com o gabarito, incluindo o campo Value. Em seguida, ampliaria os testes de concorrência para sequências mais longas com substituição, verificaria falhas em diferentes pontos de criação de threads e executaria a compilação em macOS ou outro Unix.')
p('Também mediria separadamente o custo da versão sequencial e da criação de 16 threads por acesso. Isso permitiria explicar quantitativamente o efeito da paralelização pedida, sem assumir que a busca será mais rápida. Uma avaliação posterior poderia comparar a abordagem atual com trabalhadores persistentes, preservando o requisito de uma thread por entrada.')
h('Limitações e pendências')
table([
    ['Aspecto', 'Limitação registrada'],
    ['Binário original', 'Não disponível; bytes do gabarito não comparados.'],
    ['Cobertura de concorrência', 'Saídas repetidas e caso curto em Helgrind não cobrem todas as intercalações.'],
    ['Falhas de threads', 'Criação parcial exercitada; falha em pthread_join não foi injetada.'],
    ['Plataformas', 'Linux/WSL e Windows testados; Unix/macOS não executados.'],
    ['Desempenho', 'Não houve benchmark nem comprovação de aceleração.'],
    ['Revisão manual do aluno', 'Não há registro independente nesta conversa.'],
], [140, 367])
p('<b>Entrega:</b> Classroom: lhcv.pdf e lhcv.tar, separadamente. O TAR contém apenas lhcv/vm.c e lhcv/Makefile. GitHub: código, Makefile, README.md, evidencias.log, relatório, testes e scripts auxiliares. Executáveis, anexos do professor e correct.txt não são versionados.')
p('<b>Referências técnicas:</b> enunciado 06_vm.docx.pdf e anexos addresses.txt e correct.txt da atividade 7 - VM. Base indicada pelo enunciado: Silberschatz et al., Operating System Concepts, 10ª edição, Designing a Virtual Memory Manager, p. P-51.')
p('<b>Modelo de apresentação:</b> relatórios anteriores lhcv.pdf das implementações de Deadlock e Sincronização. Foram preservados a identificação, a sequência de dez seções, as tabelas em cinza, a tipografia e a numeração de páginas. O conteúdo técnico e as evidências correspondem ao projeto de memória virtual.')


def footer(canvas, document):
    canvas.saveState()
    canvas.setFont('Helvetica', 8)
    canvas.drawString(44, 25, 'LHCV | Implementação 7 - Memória Virtual')
    canvas.drawRightString(551, 25, str(document.page))
    canvas.restoreState()


SimpleDocTemplate(
    str(root / 'lhcv.pdf'), pagesize=(595.28, 841.89),
    leftMargin=44, rightMargin=44, topMargin=32, bottomMargin=42,
    title='Relatório - Implementação 7: Memória Virtual',
    author='Luiz Henrique Carvalho Vieira',
).build(story, onFirstPage=footer, onLaterPages=footer)
print('Created lhcv.pdf')
