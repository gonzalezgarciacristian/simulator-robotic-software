// Generated from e:\Asignaturas\Cuarto\TFG\SimuladorSoftwareRobots\simulator\compiler\ArduinoGrammar.g4 by ANTLR 4.8
import org.antlr.v4.runtime.Lexer;
import org.antlr.v4.runtime.CharStream;
import org.antlr.v4.runtime.Token;
import org.antlr.v4.runtime.TokenStream;
import org.antlr.v4.runtime.*;
import org.antlr.v4.runtime.atn.*;
import org.antlr.v4.runtime.dfa.DFA;
import org.antlr.v4.runtime.misc.*;

@SuppressWarnings({"all", "warnings", "unchecked", "unused", "cast"})
public class GrammarLexer extends Lexer {
	static { RuntimeMetaData.checkVersion("4.8", RuntimeMetaData.VERSION); }

	protected static final DFA[] _decisionToDFA;
	protected static final PredictionContextCache _sharedContextCache =
		new PredictionContextCache();
	public static final int
		T__0=1, T__1=2, T__2=3, T__3=4, T__4=5, T__5=6, T__6=7, T__7=8, T__8=9, 
		T__9=10, T__10=11, T__11=12, T__12=13, T__13=14, T__14=15, T__15=16, T__16=17, 
		T__17=18, T__18=19, T__19=20, T__20=21, T__21=22, T__22=23, T__23=24, 
		T__24=25, T__25=26, T__26=27, T__27=28, T__28=29, T__29=30, T__30=31, 
		T__31=32, T__32=33, T__33=34, T__34=35, T__35=36, T__36=37, T__37=38, 
		T__38=39, T__39=40, T__40=41, T__41=42, T__42=43, T__43=44, T__44=45, 
		T__45=46, T__46=47, T__47=48, T__48=49, T__49=50, T__50=51, T__51=52, 
		T__52=53, T__53=54, T__54=55, T__55=56, T__56=57, T__57=58, T__58=59, 
		T__59=60, T__60=61, T__61=62, T__62=63, T__63=64, T__64=65, T__65=66, 
		T__66=67, ID=68, INT_CONST=69, FLOAT_CONST=70, CHAR_CONST=71, STRING_CONST=72, 
		LINE_COMMENT=73, MULTILINE_COMMENT=74, WHITESPACE=75;
	public static String[] channelNames = {
		"DEFAULT_TOKEN_CHANNEL", "HIDDEN"
	};

	public static String[] modeNames = {
		"DEFAULT_MODE"
	};

	private static String[] makeRuleNames() {
		return new String[] {
			"T__0", "T__1", "T__2", "T__3", "T__4", "T__5", "T__6", "T__7", "T__8", 
			"T__9", "T__10", "T__11", "T__12", "T__13", "T__14", "T__15", "T__16", 
			"T__17", "T__18", "T__19", "T__20", "T__21", "T__22", "T__23", "T__24", 
			"T__25", "T__26", "T__27", "T__28", "T__29", "T__30", "T__31", "T__32", 
			"T__33", "T__34", "T__35", "T__36", "T__37", "T__38", "T__39", "T__40", 
			"T__41", "T__42", "T__43", "T__44", "T__45", "T__46", "T__47", "T__48", 
			"T__49", "T__50", "T__51", "T__52", "T__53", "T__54", "T__55", "T__56", 
			"T__57", "T__58", "T__59", "T__60", "T__61", "T__62", "T__63", "T__64", 
			"T__65", "T__66", "ID", "INT_CONST", "FLOAT_CONST", "CHAR_CONST", "STRING_CONST", 
			"LINE_COMMENT", "MULTILINE_COMMENT", "WHITESPACE"
		};
	}
	public static final String[] ruleNames = makeRuleNames();

	private static String[] makeLiteralNames() {
		return new String[] {
			null, "'#include('", "')'", "'.'", "';'", "'='", "'const'", "'#define'", 
			"'bool'", "'boolean'", "'byte'", "'char'", "'double'", "'float'", "'int'", 
			"'long'", "'short'", "'size_t'", "'string'", "'unsigned int'", "'unsigned char'", 
			"'unsigned long'", "'void'", "'word'", "'setup'", "'('", "'['", "']'", 
			"'loop'", "'goto'", "'break'", "'continue'", "'while'", "'do'", "'for'", 
			"'if'", "'else'", "'switch'", "'case'", "':'", "'default'", "'*'", "'/'", 
			"'+'", "'-'", "'!='", "'=='", "'>'", "'>='", "'<='", "'<'", "'%='", "'&='", 
			"'*='", "'+='", "'-='", "'/='", "'^='", "'|='", "'&&'", "'||'", "'!'", 
			"'true'", "'false'", "'++'", "'--'", "','", "'static'"
		};
	}
	private static final String[] _LITERAL_NAMES = makeLiteralNames();
	private static String[] makeSymbolicNames() {
		return new String[] {
			null, null, null, null, null, null, null, null, null, null, null, null, 
			null, null, null, null, null, null, null, null, null, null, null, null, 
			null, null, null, null, null, null, null, null, null, null, null, null, 
			null, null, null, null, null, null, null, null, null, null, null, null, 
			null, null, null, null, null, null, null, null, null, null, null, null, 
			null, null, null, null, null, null, null, null, "ID", "INT_CONST", "FLOAT_CONST", 
			"CHAR_CONST", "STRING_CONST", "LINE_COMMENT", "MULTILINE_COMMENT", "WHITESPACE"
		};
	}
	private static final String[] _SYMBOLIC_NAMES = makeSymbolicNames();
	public static final Vocabulary VOCABULARY = new VocabularyImpl(_LITERAL_NAMES, _SYMBOLIC_NAMES);

	/**
	 * @deprecated Use {@link #VOCABULARY} instead.
	 */
	@Deprecated
	public static final String[] tokenNames;
	static {
		tokenNames = new String[_SYMBOLIC_NAMES.length];
		for (int i = 0; i < tokenNames.length; i++) {
			tokenNames[i] = VOCABULARY.getLiteralName(i);
			if (tokenNames[i] == null) {
				tokenNames[i] = VOCABULARY.getSymbolicName(i);
			}

			if (tokenNames[i] == null) {
				tokenNames[i] = "<INVALID>";
			}
		}
	}

	@Override
	@Deprecated
	public String[] getTokenNames() {
		return tokenNames;
	}

	@Override

	public Vocabulary getVocabulary() {
		return VOCABULARY;
	}


	public GrammarLexer(CharStream input) {
		super(input);
		_interp = new LexerATNSimulator(this,_ATN,_decisionToDFA,_sharedContextCache);
	}

	@Override
	public String getGrammarFileName() { return "ArduinoGrammar.g4"; }

	@Override
	public String[] getRuleNames() { return ruleNames; }

	@Override
	public String getSerializedATN() { return _serializedATN; }

	@Override
	public String[] getChannelNames() { return channelNames; }

	@Override
	public String[] getModeNames() { return modeNames; }

	@Override
	public ATN getATN() { return _ATN; }

	public static final String _serializedATN =
		"\3\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964\2M\u0211\b\1\4\2\t"+
		"\2\4\3\t\3\4\4\t\4\4\5\t\5\4\6\t\6\4\7\t\7\4\b\t\b\4\t\t\t\4\n\t\n\4\13"+
		"\t\13\4\f\t\f\4\r\t\r\4\16\t\16\4\17\t\17\4\20\t\20\4\21\t\21\4\22\t\22"+
		"\4\23\t\23\4\24\t\24\4\25\t\25\4\26\t\26\4\27\t\27\4\30\t\30\4\31\t\31"+
		"\4\32\t\32\4\33\t\33\4\34\t\34\4\35\t\35\4\36\t\36\4\37\t\37\4 \t \4!"+
		"\t!\4\"\t\"\4#\t#\4$\t$\4%\t%\4&\t&\4\'\t\'\4(\t(\4)\t)\4*\t*\4+\t+\4"+
		",\t,\4-\t-\4.\t.\4/\t/\4\60\t\60\4\61\t\61\4\62\t\62\4\63\t\63\4\64\t"+
		"\64\4\65\t\65\4\66\t\66\4\67\t\67\48\t8\49\t9\4:\t:\4;\t;\4<\t<\4=\t="+
		"\4>\t>\4?\t?\4@\t@\4A\tA\4B\tB\4C\tC\4D\tD\4E\tE\4F\tF\4G\tG\4H\tH\4I"+
		"\tI\4J\tJ\4K\tK\4L\tL\3\2\3\2\3\2\3\2\3\2\3\2\3\2\3\2\3\2\3\2\3\3\3\3"+
		"\3\4\3\4\3\5\3\5\3\6\3\6\3\7\3\7\3\7\3\7\3\7\3\7\3\b\3\b\3\b\3\b\3\b\3"+
		"\b\3\b\3\b\3\t\3\t\3\t\3\t\3\t\3\n\3\n\3\n\3\n\3\n\3\n\3\n\3\n\3\13\3"+
		"\13\3\13\3\13\3\13\3\f\3\f\3\f\3\f\3\f\3\r\3\r\3\r\3\r\3\r\3\r\3\r\3\16"+
		"\3\16\3\16\3\16\3\16\3\16\3\17\3\17\3\17\3\17\3\20\3\20\3\20\3\20\3\20"+
		"\3\21\3\21\3\21\3\21\3\21\3\21\3\22\3\22\3\22\3\22\3\22\3\22\3\22\3\23"+
		"\3\23\3\23\3\23\3\23\3\23\3\23\3\24\3\24\3\24\3\24\3\24\3\24\3\24\3\24"+
		"\3\24\3\24\3\24\3\24\3\24\3\25\3\25\3\25\3\25\3\25\3\25\3\25\3\25\3\25"+
		"\3\25\3\25\3\25\3\25\3\25\3\26\3\26\3\26\3\26\3\26\3\26\3\26\3\26\3\26"+
		"\3\26\3\26\3\26\3\26\3\26\3\27\3\27\3\27\3\27\3\27\3\30\3\30\3\30\3\30"+
		"\3\30\3\31\3\31\3\31\3\31\3\31\3\31\3\32\3\32\3\33\3\33\3\34\3\34\3\35"+
		"\3\35\3\35\3\35\3\35\3\36\3\36\3\36\3\36\3\36\3\37\3\37\3\37\3\37\3\37"+
		"\3\37\3 \3 \3 \3 \3 \3 \3 \3 \3 \3!\3!\3!\3!\3!\3!\3\"\3\"\3\"\3#\3#\3"+
		"#\3#\3$\3$\3$\3%\3%\3%\3%\3%\3&\3&\3&\3&\3&\3&\3&\3\'\3\'\3\'\3\'\3\'"+
		"\3(\3(\3)\3)\3)\3)\3)\3)\3)\3)\3*\3*\3+\3+\3,\3,\3-\3-\3.\3.\3.\3/\3/"+
		"\3/\3\60\3\60\3\61\3\61\3\61\3\62\3\62\3\62\3\63\3\63\3\64\3\64\3\64\3"+
		"\65\3\65\3\65\3\66\3\66\3\66\3\67\3\67\3\67\38\38\38\39\39\39\3:\3:\3"+
		":\3;\3;\3;\3<\3<\3<\3=\3=\3=\3>\3>\3?\3?\3?\3?\3?\3@\3@\3@\3@\3@\3@\3"+
		"A\3A\3A\3B\3B\3B\3C\3C\3D\3D\3D\3D\3D\3D\3D\3E\3E\7E\u01d2\nE\fE\16E\u01d5"+
		"\13E\3F\6F\u01d8\nF\rF\16F\u01d9\3G\6G\u01dd\nG\rG\16G\u01de\3G\3G\6G"+
		"\u01e3\nG\rG\16G\u01e4\3H\3H\3H\3H\3I\3I\3I\3I\3J\3J\3J\3J\7J\u01f3\n"+
		"J\fJ\16J\u01f6\13J\3J\5J\u01f9\nJ\3J\3J\3K\3K\3K\3K\7K\u0201\nK\fK\16"+
		"K\u0204\13K\3K\3K\3K\3K\3K\3L\6L\u020c\nL\rL\16L\u020d\3L\3L\4\u01f4\u0202"+
		"\2M\3\3\5\4\7\5\t\6\13\7\r\b\17\t\21\n\23\13\25\f\27\r\31\16\33\17\35"+
		"\20\37\21!\22#\23%\24\'\25)\26+\27-\30/\31\61\32\63\33\65\34\67\359\36"+
		";\37= ?!A\"C#E$G%I&K\'M(O)Q*S+U,W-Y.[/]\60_\61a\62c\63e\64g\65i\66k\67"+
		"m8o9q:s;u<w=y>{?}@\177A\u0081B\u0083C\u0085D\u0087E\u0089F\u008bG\u008d"+
		"H\u008fI\u0091J\u0093K\u0095L\u0097M\3\2\t\5\2C\\aac|\6\2\62;C\\aac|\3"+
		"\2\62;\5\2\f\f))^^\5\2\f\f$$^^\3\3\f\f\5\2\13\f\17\17\"\"\2\u0217\2\3"+
		"\3\2\2\2\2\5\3\2\2\2\2\7\3\2\2\2\2\t\3\2\2\2\2\13\3\2\2\2\2\r\3\2\2\2"+
		"\2\17\3\2\2\2\2\21\3\2\2\2\2\23\3\2\2\2\2\25\3\2\2\2\2\27\3\2\2\2\2\31"+
		"\3\2\2\2\2\33\3\2\2\2\2\35\3\2\2\2\2\37\3\2\2\2\2!\3\2\2\2\2#\3\2\2\2"+
		"\2%\3\2\2\2\2\'\3\2\2\2\2)\3\2\2\2\2+\3\2\2\2\2-\3\2\2\2\2/\3\2\2\2\2"+
		"\61\3\2\2\2\2\63\3\2\2\2\2\65\3\2\2\2\2\67\3\2\2\2\29\3\2\2\2\2;\3\2\2"+
		"\2\2=\3\2\2\2\2?\3\2\2\2\2A\3\2\2\2\2C\3\2\2\2\2E\3\2\2\2\2G\3\2\2\2\2"+
		"I\3\2\2\2\2K\3\2\2\2\2M\3\2\2\2\2O\3\2\2\2\2Q\3\2\2\2\2S\3\2\2\2\2U\3"+
		"\2\2\2\2W\3\2\2\2\2Y\3\2\2\2\2[\3\2\2\2\2]\3\2\2\2\2_\3\2\2\2\2a\3\2\2"+
		"\2\2c\3\2\2\2\2e\3\2\2\2\2g\3\2\2\2\2i\3\2\2\2\2k\3\2\2\2\2m\3\2\2\2\2"+
		"o\3\2\2\2\2q\3\2\2\2\2s\3\2\2\2\2u\3\2\2\2\2w\3\2\2\2\2y\3\2\2\2\2{\3"+
		"\2\2\2\2}\3\2\2\2\2\177\3\2\2\2\2\u0081\3\2\2\2\2\u0083\3\2\2\2\2\u0085"+
		"\3\2\2\2\2\u0087\3\2\2\2\2\u0089\3\2\2\2\2\u008b\3\2\2\2\2\u008d\3\2\2"+
		"\2\2\u008f\3\2\2\2\2\u0091\3\2\2\2\2\u0093\3\2\2\2\2\u0095\3\2\2\2\2\u0097"+
		"\3\2\2\2\3\u0099\3\2\2\2\5\u00a3\3\2\2\2\7\u00a5\3\2\2\2\t\u00a7\3\2\2"+
		"\2\13\u00a9\3\2\2\2\r\u00ab\3\2\2\2\17\u00b1\3\2\2\2\21\u00b9\3\2\2\2"+
		"\23\u00be\3\2\2\2\25\u00c6\3\2\2\2\27\u00cb\3\2\2\2\31\u00d0\3\2\2\2\33"+
		"\u00d7\3\2\2\2\35\u00dd\3\2\2\2\37\u00e1\3\2\2\2!\u00e6\3\2\2\2#\u00ec"+
		"\3\2\2\2%\u00f3\3\2\2\2\'\u00fa\3\2\2\2)\u0107\3\2\2\2+\u0115\3\2\2\2"+
		"-\u0123\3\2\2\2/\u0128\3\2\2\2\61\u012d\3\2\2\2\63\u0133\3\2\2\2\65\u0135"+
		"\3\2\2\2\67\u0137\3\2\2\29\u0139\3\2\2\2;\u013e\3\2\2\2=\u0143\3\2\2\2"+
		"?\u0149\3\2\2\2A\u0152\3\2\2\2C\u0158\3\2\2\2E\u015b\3\2\2\2G\u015f\3"+
		"\2\2\2I\u0162\3\2\2\2K\u0167\3\2\2\2M\u016e\3\2\2\2O\u0173\3\2\2\2Q\u0175"+
		"\3\2\2\2S\u017d\3\2\2\2U\u017f\3\2\2\2W\u0181\3\2\2\2Y\u0183\3\2\2\2["+
		"\u0185\3\2\2\2]\u0188\3\2\2\2_\u018b\3\2\2\2a\u018d\3\2\2\2c\u0190\3\2"+
		"\2\2e\u0193\3\2\2\2g\u0195\3\2\2\2i\u0198\3\2\2\2k\u019b\3\2\2\2m\u019e"+
		"\3\2\2\2o\u01a1\3\2\2\2q\u01a4\3\2\2\2s\u01a7\3\2\2\2u\u01aa\3\2\2\2w"+
		"\u01ad\3\2\2\2y\u01b0\3\2\2\2{\u01b3\3\2\2\2}\u01b5\3\2\2\2\177\u01ba"+
		"\3\2\2\2\u0081\u01c0\3\2\2\2\u0083\u01c3\3\2\2\2\u0085\u01c6\3\2\2\2\u0087"+
		"\u01c8\3\2\2\2\u0089\u01cf\3\2\2\2\u008b\u01d7\3\2\2\2\u008d\u01dc\3\2"+
		"\2\2\u008f\u01e6\3\2\2\2\u0091\u01ea\3\2\2\2\u0093\u01ee\3\2\2\2\u0095"+
		"\u01fc\3\2\2\2\u0097\u020b\3\2\2\2\u0099\u009a\7%\2\2\u009a\u009b\7k\2"+
		"\2\u009b\u009c\7p\2\2\u009c\u009d\7e\2\2\u009d\u009e\7n\2\2\u009e\u009f"+
		"\7w\2\2\u009f\u00a0\7f\2\2\u00a0\u00a1\7g\2\2\u00a1\u00a2\7*\2\2\u00a2"+
		"\4\3\2\2\2\u00a3\u00a4\7+\2\2\u00a4\6\3\2\2\2\u00a5\u00a6\7\60\2\2\u00a6"+
		"\b\3\2\2\2\u00a7\u00a8\7=\2\2\u00a8\n\3\2\2\2\u00a9\u00aa\7?\2\2\u00aa"+
		"\f\3\2\2\2\u00ab\u00ac\7e\2\2\u00ac\u00ad\7q\2\2\u00ad\u00ae\7p\2\2\u00ae"+
		"\u00af\7u\2\2\u00af\u00b0\7v\2\2\u00b0\16\3\2\2\2\u00b1\u00b2\7%\2\2\u00b2"+
		"\u00b3\7f\2\2\u00b3\u00b4\7g\2\2\u00b4\u00b5\7h\2\2\u00b5\u00b6\7k\2\2"+
		"\u00b6\u00b7\7p\2\2\u00b7\u00b8\7g\2\2\u00b8\20\3\2\2\2\u00b9\u00ba\7"+
		"d\2\2\u00ba\u00bb\7q\2\2\u00bb\u00bc\7q\2\2\u00bc\u00bd\7n\2\2\u00bd\22"+
		"\3\2\2\2\u00be\u00bf\7d\2\2\u00bf\u00c0\7q\2\2\u00c0\u00c1\7q\2\2\u00c1"+
		"\u00c2\7n\2\2\u00c2\u00c3\7g\2\2\u00c3\u00c4\7c\2\2\u00c4\u00c5\7p\2\2"+
		"\u00c5\24\3\2\2\2\u00c6\u00c7\7d\2\2\u00c7\u00c8\7{\2\2\u00c8\u00c9\7"+
		"v\2\2\u00c9\u00ca\7g\2\2\u00ca\26\3\2\2\2\u00cb\u00cc\7e\2\2\u00cc\u00cd"+
		"\7j\2\2\u00cd\u00ce\7c\2\2\u00ce\u00cf\7t\2\2\u00cf\30\3\2\2\2\u00d0\u00d1"+
		"\7f\2\2\u00d1\u00d2\7q\2\2\u00d2\u00d3\7w\2\2\u00d3\u00d4\7d\2\2\u00d4"+
		"\u00d5\7n\2\2\u00d5\u00d6\7g\2\2\u00d6\32\3\2\2\2\u00d7\u00d8\7h\2\2\u00d8"+
		"\u00d9\7n\2\2\u00d9\u00da\7q\2\2\u00da\u00db\7c\2\2\u00db\u00dc\7v\2\2"+
		"\u00dc\34\3\2\2\2\u00dd\u00de\7k\2\2\u00de\u00df\7p\2\2\u00df\u00e0\7"+
		"v\2\2\u00e0\36\3\2\2\2\u00e1\u00e2\7n\2\2\u00e2\u00e3\7q\2\2\u00e3\u00e4"+
		"\7p\2\2\u00e4\u00e5\7i\2\2\u00e5 \3\2\2\2\u00e6\u00e7\7u\2\2\u00e7\u00e8"+
		"\7j\2\2\u00e8\u00e9\7q\2\2\u00e9\u00ea\7t\2\2\u00ea\u00eb\7v\2\2\u00eb"+
		"\"\3\2\2\2\u00ec\u00ed\7u\2\2\u00ed\u00ee\7k\2\2\u00ee\u00ef\7|\2\2\u00ef"+
		"\u00f0\7g\2\2\u00f0\u00f1\7a\2\2\u00f1\u00f2\7v\2\2\u00f2$\3\2\2\2\u00f3"+
		"\u00f4\7u\2\2\u00f4\u00f5\7v\2\2\u00f5\u00f6\7t\2\2\u00f6\u00f7\7k\2\2"+
		"\u00f7\u00f8\7p\2\2\u00f8\u00f9\7i\2\2\u00f9&\3\2\2\2\u00fa\u00fb\7w\2"+
		"\2\u00fb\u00fc\7p\2\2\u00fc\u00fd\7u\2\2\u00fd\u00fe\7k\2\2\u00fe\u00ff"+
		"\7i\2\2\u00ff\u0100\7p\2\2\u0100\u0101\7g\2\2\u0101\u0102\7f\2\2\u0102"+
		"\u0103\7\"\2\2\u0103\u0104\7k\2\2\u0104\u0105\7p\2\2\u0105\u0106\7v\2"+
		"\2\u0106(\3\2\2\2\u0107\u0108\7w\2\2\u0108\u0109\7p\2\2\u0109\u010a\7"+
		"u\2\2\u010a\u010b\7k\2\2\u010b\u010c\7i\2\2\u010c\u010d\7p\2\2\u010d\u010e"+
		"\7g\2\2\u010e\u010f\7f\2\2\u010f\u0110\7\"\2\2\u0110\u0111\7e\2\2\u0111"+
		"\u0112\7j\2\2\u0112\u0113\7c\2\2\u0113\u0114\7t\2\2\u0114*\3\2\2\2\u0115"+
		"\u0116\7w\2\2\u0116\u0117\7p\2\2\u0117\u0118\7u\2\2\u0118\u0119\7k\2\2"+
		"\u0119\u011a\7i\2\2\u011a\u011b\7p\2\2\u011b\u011c\7g\2\2\u011c\u011d"+
		"\7f\2\2\u011d\u011e\7\"\2\2\u011e\u011f\7n\2\2\u011f\u0120\7q\2\2\u0120"+
		"\u0121\7p\2\2\u0121\u0122\7i\2\2\u0122,\3\2\2\2\u0123\u0124\7x\2\2\u0124"+
		"\u0125\7q\2\2\u0125\u0126\7k\2\2\u0126\u0127\7f\2\2\u0127.\3\2\2\2\u0128"+
		"\u0129\7y\2\2\u0129\u012a\7q\2\2\u012a\u012b\7t\2\2\u012b\u012c\7f\2\2"+
		"\u012c\60\3\2\2\2\u012d\u012e\7u\2\2\u012e\u012f\7g\2\2\u012f\u0130\7"+
		"v\2\2\u0130\u0131\7w\2\2\u0131\u0132\7r\2\2\u0132\62\3\2\2\2\u0133\u0134"+
		"\7*\2\2\u0134\64\3\2\2\2\u0135\u0136\7]\2\2\u0136\66\3\2\2\2\u0137\u0138"+
		"\7_\2\2\u01388\3\2\2\2\u0139\u013a\7n\2\2\u013a\u013b\7q\2\2\u013b\u013c"+
		"\7q\2\2\u013c\u013d\7r\2\2\u013d:\3\2\2\2\u013e\u013f\7i\2\2\u013f\u0140"+
		"\7q\2\2\u0140\u0141\7v\2\2\u0141\u0142\7q\2\2\u0142<\3\2\2\2\u0143\u0144"+
		"\7d\2\2\u0144\u0145\7t\2\2\u0145\u0146\7g\2\2\u0146\u0147\7c\2\2\u0147"+
		"\u0148\7m\2\2\u0148>\3\2\2\2\u0149\u014a\7e\2\2\u014a\u014b\7q\2\2\u014b"+
		"\u014c\7p\2\2\u014c\u014d\7v\2\2\u014d\u014e\7k\2\2\u014e\u014f\7p\2\2"+
		"\u014f\u0150\7w\2\2\u0150\u0151\7g\2\2\u0151@\3\2\2\2\u0152\u0153\7y\2"+
		"\2\u0153\u0154\7j\2\2\u0154\u0155\7k\2\2\u0155\u0156\7n\2\2\u0156\u0157"+
		"\7g\2\2\u0157B\3\2\2\2\u0158\u0159\7f\2\2\u0159\u015a\7q\2\2\u015aD\3"+
		"\2\2\2\u015b\u015c\7h\2\2\u015c\u015d\7q\2\2\u015d\u015e\7t\2\2\u015e"+
		"F\3\2\2\2\u015f\u0160\7k\2\2\u0160\u0161\7h\2\2\u0161H\3\2\2\2\u0162\u0163"+
		"\7g\2\2\u0163\u0164\7n\2\2\u0164\u0165\7u\2\2\u0165\u0166\7g\2\2\u0166"+
		"J\3\2\2\2\u0167\u0168\7u\2\2\u0168\u0169\7y\2\2\u0169\u016a\7k\2\2\u016a"+
		"\u016b\7v\2\2\u016b\u016c\7e\2\2\u016c\u016d\7j\2\2\u016dL\3\2\2\2\u016e"+
		"\u016f\7e\2\2\u016f\u0170\7c\2\2\u0170\u0171\7u\2\2\u0171\u0172\7g\2\2"+
		"\u0172N\3\2\2\2\u0173\u0174\7<\2\2\u0174P\3\2\2\2\u0175\u0176\7f\2\2\u0176"+
		"\u0177\7g\2\2\u0177\u0178\7h\2\2\u0178\u0179\7c\2\2\u0179\u017a\7w\2\2"+
		"\u017a\u017b\7n\2\2\u017b\u017c\7v\2\2\u017cR\3\2\2\2\u017d\u017e\7,\2"+
		"\2\u017eT\3\2\2\2\u017f\u0180\7\61\2\2\u0180V\3\2\2\2\u0181\u0182\7-\2"+
		"\2\u0182X\3\2\2\2\u0183\u0184\7/\2\2\u0184Z\3\2\2\2\u0185\u0186\7#\2\2"+
		"\u0186\u0187\7?\2\2\u0187\\\3\2\2\2\u0188\u0189\7?\2\2\u0189\u018a\7?"+
		"\2\2\u018a^\3\2\2\2\u018b\u018c\7@\2\2\u018c`\3\2\2\2\u018d\u018e\7@\2"+
		"\2\u018e\u018f\7?\2\2\u018fb\3\2\2\2\u0190\u0191\7>\2\2\u0191\u0192\7"+
		"?\2\2\u0192d\3\2\2\2\u0193\u0194\7>\2\2\u0194f\3\2\2\2\u0195\u0196\7\'"+
		"\2\2\u0196\u0197\7?\2\2\u0197h\3\2\2\2\u0198\u0199\7(\2\2\u0199\u019a"+
		"\7?\2\2\u019aj\3\2\2\2\u019b\u019c\7,\2\2\u019c\u019d\7?\2\2\u019dl\3"+
		"\2\2\2\u019e\u019f\7-\2\2\u019f\u01a0\7?\2\2\u01a0n\3\2\2\2\u01a1\u01a2"+
		"\7/\2\2\u01a2\u01a3\7?\2\2\u01a3p\3\2\2\2\u01a4\u01a5\7\61\2\2\u01a5\u01a6"+
		"\7?\2\2\u01a6r\3\2\2\2\u01a7\u01a8\7`\2\2\u01a8\u01a9\7?\2\2\u01a9t\3"+
		"\2\2\2\u01aa\u01ab\7~\2\2\u01ab\u01ac\7?\2\2\u01acv\3\2\2\2\u01ad\u01ae"+
		"\7(\2\2\u01ae\u01af\7(\2\2\u01afx\3\2\2\2\u01b0\u01b1\7~\2\2\u01b1\u01b2"+
		"\7~\2\2\u01b2z\3\2\2\2\u01b3\u01b4\7#\2\2\u01b4|\3\2\2\2\u01b5\u01b6\7"+
		"v\2\2\u01b6\u01b7\7t\2\2\u01b7\u01b8\7w\2\2\u01b8\u01b9\7g\2\2\u01b9~"+
		"\3\2\2\2\u01ba\u01bb\7h\2\2\u01bb\u01bc\7c\2\2\u01bc\u01bd\7n\2\2\u01bd"+
		"\u01be\7u\2\2\u01be\u01bf\7g\2\2\u01bf\u0080\3\2\2\2\u01c0\u01c1\7-\2"+
		"\2\u01c1\u01c2\7-\2\2\u01c2\u0082\3\2\2\2\u01c3\u01c4\7/\2\2\u01c4\u01c5"+
		"\7/\2\2\u01c5\u0084\3\2\2\2\u01c6\u01c7\7.\2\2\u01c7\u0086\3\2\2\2\u01c8"+
		"\u01c9\7u\2\2\u01c9\u01ca\7v\2\2\u01ca\u01cb\7c\2\2\u01cb\u01cc\7v\2\2"+
		"\u01cc\u01cd\7k\2\2\u01cd\u01ce\7e\2\2\u01ce\u0088\3\2\2\2\u01cf\u01d3"+
		"\t\2\2\2\u01d0\u01d2\t\3\2\2\u01d1\u01d0\3\2\2\2\u01d2\u01d5\3\2\2\2\u01d3"+
		"\u01d1\3\2\2\2\u01d3\u01d4\3\2\2\2\u01d4\u008a\3\2\2\2\u01d5\u01d3\3\2"+
		"\2\2\u01d6\u01d8\t\4\2\2\u01d7\u01d6\3\2\2\2\u01d8\u01d9\3\2\2\2\u01d9"+
		"\u01d7\3\2\2\2\u01d9\u01da\3\2\2\2\u01da\u008c\3\2\2\2\u01db\u01dd\t\4"+
		"\2\2\u01dc\u01db\3\2\2\2\u01dd\u01de\3\2\2\2\u01de\u01dc\3\2\2\2\u01de"+
		"\u01df\3\2\2\2\u01df\u01e0\3\2\2\2\u01e0\u01e2\7\60\2\2\u01e1\u01e3\t"+
		"\4\2\2\u01e2\u01e1\3\2\2\2\u01e3\u01e4\3\2\2\2\u01e4\u01e2\3\2\2\2\u01e4"+
		"\u01e5\3\2\2\2\u01e5\u008e\3\2\2\2\u01e6\u01e7\7)\2\2\u01e7\u01e8\n\5"+
		"\2\2\u01e8\u01e9\7)\2\2\u01e9\u0090\3\2\2\2\u01ea\u01eb\7$\2\2\u01eb\u01ec"+
		"\n\6\2\2\u01ec\u01ed\7$\2\2\u01ed\u0092\3\2\2\2\u01ee\u01ef\7\61\2\2\u01ef"+
		"\u01f0\7\61\2\2\u01f0\u01f4\3\2\2\2\u01f1\u01f3\13\2\2\2\u01f2\u01f1\3"+
		"\2\2\2\u01f3\u01f6\3\2\2\2\u01f4\u01f5\3\2\2\2\u01f4\u01f2\3\2\2\2\u01f5"+
		"\u01f8\3\2\2\2\u01f6\u01f4\3\2\2\2\u01f7\u01f9\t\7\2\2\u01f8\u01f7\3\2"+
		"\2\2\u01f9\u01fa\3\2\2\2\u01fa\u01fb\bJ\2\2\u01fb\u0094\3\2\2\2\u01fc"+
		"\u01fd\7\61\2\2\u01fd\u01fe\7,\2\2\u01fe\u0202\3\2\2\2\u01ff\u0201\13"+
		"\2\2\2\u0200\u01ff\3\2\2\2\u0201\u0204\3\2\2\2\u0202\u0203\3\2\2\2\u0202"+
		"\u0200\3\2\2\2\u0203\u0205\3\2\2\2\u0204\u0202\3\2\2\2\u0205\u0206\7,"+
		"\2\2\u0206\u0207\7\61\2\2\u0207\u0208\3\2\2\2\u0208\u0209\bK\2\2\u0209"+
		"\u0096\3\2\2\2\u020a\u020c\t\b\2\2\u020b\u020a\3\2\2\2\u020c\u020d\3\2"+
		"\2\2\u020d\u020b\3\2\2\2\u020d\u020e\3\2\2\2\u020e\u020f\3\2\2\2\u020f"+
		"\u0210\bL\2\2\u0210\u0098\3\2\2\2\13\2\u01d3\u01d9\u01de\u01e4\u01f4\u01f8"+
		"\u0202\u020d\3\b\2\2";
	public static final ATN _ATN =
		new ATNDeserializer().deserialize(_serializedATN.toCharArray());
	static {
		_decisionToDFA = new DFA[_ATN.getNumberOfDecisions()];
		for (int i = 0; i < _ATN.getNumberOfDecisions(); i++) {
			_decisionToDFA[i] = new DFA(_ATN.getDecisionState(i), i);
		}
	}
}