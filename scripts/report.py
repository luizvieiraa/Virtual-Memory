"""Generate the delivery report. Requires reportlab (not needed to build vm)."""
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

root = Path(__file__).resolve().parents[1]
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyReport', fontName='Helvetica', fontSize=10.5,
                         leading=15, spaceAfter=10, textColor=colors.HexColor('#243247')))
styles.add(ParagraphStyle(name='SectionReport', fontName='Helvetica-Bold', fontSize=14,
                         leading=18, spaceBefore=12, spaceAfter=10, textColor=colors.HexColor('#163b5c')))
styles.add(ParagraphStyle(name='CodeReport', fontName='Courier', fontSize=9,
                         leading=13, spaceAfter=10))
story = []

def paragraph(text):
    story.append(Paragraph(text, styles['BodyReport']))

def section(text):
    story.append(Paragraph(text, styles['SectionReport']))

def table(rows, widths):
    rows = [[Paragraph(str(cell), styles['BodyReport']) for cell in row] for row in rows]
    result = Table(rows, colWidths=widths, hAlign='LEFT')
    result.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8eff5')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEBELOW', (0, 0), (-1, 0), 0.8, colors.HexColor('#8ca3b6')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
    ]))
    story.append(result)

story.append(Paragraph('Memória virtual', styles['Title']))
paragraph('<b>Implementação 7 - Infraestrutura de software</b><br/>Luiz Vieira | login: lhcv | 23 de novembro de 2026')
section('1. Objetivo e configuração')
paragraph('Implementar em C um gerenciador de memória virtual que traduza endereços lógicos, carregue páginas de um arquivo binário e simule substituição de páginas e TLB. A versão final utiliza 128 frames, políticas FIFO e LRU independentes e uma thread POSIX por entrada da TLB. O cabeçalho do enunciado identifica a atividade como Implementação 6; o planejamento e esta entrega seguem a identificação 7 - VM do Classroom.')
table([['Estrutura', 'Configuração'], ['Espaço lógico', '16 bits: 256 páginas de 256 bytes'], ['Memória física', '128 frames de 256 bytes: 32.768 bytes'], ['TLB', '16 entradas com página, frame, validade e marcador de uso'], ['Entrada / saída', 'Arquivo decimal por linha / correct.txt'], ['Binário de páginas', 'BACKING_STORE.bin no diretório de execução']], [145, 350])
section('2. Fluxo de tradução')
paragraph('O endereço é separado em página (endereço / 256) e deslocamento (endereço % 256). A busca paralela na TLB produz um índice ou miss. Em hit, o frame é obtido da TLB; em miss, consulta-se a tabela de páginas. Se a página não estiver residente, ocorre page fault: o programa lê 256 bytes a partir de página × 256 no backing store.')
paragraph('Frames livres são usados em ordem de 0 a 127. Depois disso, a política de páginas escolhe uma vítima; o mapeamento antigo é invalidado na tabela e na TLB. A nova tradução é inserida na TLB. O endereço físico resulta de frame × 256 + deslocamento. O byte lido é convertido explicitamente para um valor de -128 a 127, sem depender do sinal padrão de char.')
story.append(PageBreak())
section('3. Substituição e sincronização')
paragraph('<b>FIFO de páginas:</b> um índice circular indica a próxima vítima. Hits não alteram a ordem de entrada. <b>LRU de páginas:</b> posições de recência limitadas a 0..127 representam a ordem de uso. Todo acesso atualiza essa ordem, inclusive um hit na TLB.')
paragraph('<b>TLB:</b> a primeira entrada inválida é reutilizada; quando cheia, vence o menor marcador. Em FIFO, o marcador registra a inserção; em LRU, ele é atualizado em cada hit. As políticas de páginas e da TLB são selecionadas separadamente pelos argumentos.')
paragraph('<b>Threads:</b> a cada endereço, 16 threads são criadas, cada uma recebendo uma cópia de uma entrada e um resultado próprio. A thread principal chama pthread_join para todas antes de alterar a TLB ou usar os resultados. As tarefas não escrevem nas estruturas compartilhadas. Se uma criação falhar, todas as threads já iniciadas são aguardadas e a execução termina com erro. Uma falha em join encerra o processo sem reutilizar os argumentos das tarefas.')
paragraph('A paralelização atende à simulação solicitada. A criação de 16 threads para consultar apenas 16 entradas pode aumentar o tempo de execução; não foi medida nem alegada aceleração.')
section('4. Compilação, interface e erros')
story.append(Paragraph('make<br/>./vm addresses.txt lru fifo<br/>make clean', styles['CodeReport']))
paragraph('O Makefile usa C11, avisos de compilação e -pthread. A raiz do repositório contém o Makefile; após extrair o pacote, a compilação é feita dentro de lhcv/. A execução recebe exatamente três argumentos. FIFO e LRU são aceitos somente em minúsculas.')
paragraph('Há diagnóstico em stderr e retorno de falha para quantidade incorreta de argumentos, política inválida, entrada ausente ou malformada, arquivo vazio, endereço fora de 0..65535, falha de leitura do backing store, saída inacessível e falha de threads. Não há estatísticas de sucesso quando a entrada é rejeitada; arquivos parciais devem ser descartados.')
section('5. Evolução por etapas')
paragraph('Os commits preservam as versões intermediárias pedidas na rubrica: tradução e leitura de entrada; 256 frames sem TLB; 128 frames com FIFO; LRU de páginas; TLB sequencial; e busca com threads. A versão final executa o fluxo com threads. As versões anteriores podem ser consultadas pelo histórico do Git, sem alterar os arquivos da entrega final.')
story.append(PageBreak())
section('6. Validação e resultados')
paragraph('Os testes reproduzíveis em tests/test_vm.py geram um binário sintético com bytes conhecidos e usam um modelo independente baseado em ordem de páginas e entradas da TLB. Cada uma das quatro combinações executa 1.691 endereços: limites, bytes com sinal, hits, misses com página residente, invalidação, recência e múltiplas substituições, incluindo 1.000 acessos aleatórios. Todas as linhas e estatísticas são comparadas.')
paragraph('A compilação e a suíte passaram no Ubuntu via WSL e no Windows com MinGW-w64. A etapa 7 também comparou saídas com a versão sequencial em três execuções por combinação, e simulou falha de criação com cinco threads já iniciadas. O arquivo evidencias.log registra os comandos e resultados desta entrega.')
table([['Referência lru / fifo', 'Resultado'], ['Endereços traduzidos', '1000'], ['Page faults / taxa', '539 / 0.539'], ['Hits da TLB / taxa', '54 / 0.054'], ['Índices e endereços físicos', '1000 linhas conferidas']], [250, 245])
paragraph('<b>Limite da comparação:</b> os endereços e o gabarito do professor foram obtidos, mas o BACKING_STORE.bin original não estava disponível. A execução de referência usou bytes zerados e excluiu somente o campo Value da comparação. Os bytes foram validados com dados sintéticos, não com o binário original. A comparação integral com o material original permanece pendente.')
paragraph('Helgrind e Memcheck foram usados em um caso curto com hit, miss e endereço limite. A cobertura de ferramentas dinâmicas é restrita a esse caso e não constitui prova geral de ausência de erros. Unix e macOS não foram executados.')
section('7. Arquivos de entrega e reprodução')
paragraph('Para o GitHub: código, Makefile, README.md, evidencias.log e lhcv.pdf, com testes e scripts auxiliares. Para o Classroom: lhcv.pdf separado e lhcv.tar, contendo somente lhcv/vm.c e lhcv/Makefile. O arquivo tar foi extraído em um diretório temporário e compilado com make. Executáveis e anexos do professor não integram o pacote.')
paragraph('Reproduzir a suíte: make test. Gerar o pacote: make package. Comparação completa, quando o binário original estiver disponível: python3 tests/test_vm.py --addresses addresses.txt --reference gabarito.txt --backing BACKING_STORE.bin. O gabarito deve ter nome diferente de correct.txt, pois esse arquivo é sobrescrito pelo programa.')
paragraph('<b>Referências:</b> enunciado 06_vm.docx.pdf e arquivos addresses.txt/correct.txt da atividade 7 - VM no Classroom. Base indicada pelo enunciado: Silberschatz et al., Operating System Concepts, 10ª edição, exercício Designing a Virtual Memory Manager, p. P-51.')

def footer(canvas, document):
    canvas.setStrokeColor(colors.HexColor('#ccd7e0'))
    canvas.line(50, 42, A4[0] - 50, 42)
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.HexColor('#526579'))
    canvas.drawString(50, 28, 'lhcv | Implementação 7 - VM')
    canvas.drawRightString(A4[0] - 50, 28, str(document.page))

document = SimpleDocTemplate(str(root / 'lhcv.pdf'), pagesize=A4,
                             rightMargin=50, leftMargin=50, topMargin=40, bottomMargin=55,
                             title='Implementação 7 - Memória virtual', author='Luiz Vieira')
document.build(story, onFirstPage=footer, onLaterPages=footer)
print('Created lhcv.pdf')
